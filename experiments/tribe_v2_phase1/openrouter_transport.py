"""Paid OpenRouter transport guarded by an explicit budget gate."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

from .cost_estimate import decimal_price
from .prompts import build_messages


OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class PaidRunNotConfirmed(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


class OpenRouterError(RuntimeError):
    pass


@dataclass
class BudgetGate:
    max_cost_usd: Decimal
    spent_usd: Decimal = Decimal("0")
    reserved_usd: Decimal = Decimal("0")
    ledger: list[dict[str, Any]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    @classmethod
    def from_env(cls) -> "BudgetGate":
        raw = os.environ.get("TRIBE_MAX_COST_USD")
        if not raw:
            raise BudgetExceeded("TRIBE_MAX_COST_USD is required for paid runs")
        return cls(max_cost_usd=Decimal(raw))

    @property
    def remaining_usd(self) -> Decimal:
        return self.max_cost_usd - self.spent_usd - self.reserved_usd

    def reserve(self, estimate_usd: Decimal, label: str) -> Decimal:
        with self._lock:
            if estimate_usd > self.remaining_usd:
                raise BudgetExceeded(
                    f"estimated call {estimate_usd} for {label} exceeds remaining budget {self.remaining_usd}"
                )
            self.reserved_usd += estimate_usd
            return estimate_usd

    def commit(
        self,
        reserved_usd: Decimal,
        actual_usd: Decimal,
        label: str,
        usage: dict[str, Any] | None,
    ) -> None:
        with self._lock:
            self.reserved_usd -= reserved_usd
            self.spent_usd += actual_usd
            cost_alert = actual_usd > reserved_usd
            self.ledger.append(
                {
                    "label": label,
                    "reserved_usd": str(reserved_usd),
                    "actual_usd": str(actual_usd),
                    "actual_exceeded_reserved": cost_alert,
                    "spent_usd": str(self.spent_usd),
                    "remaining_usd": str(self.remaining_usd),
                    "usage": usage or {},
                }
            )

    def release(self, reserved_usd: Decimal, label: str, error: str) -> None:
        with self._lock:
            self.reserved_usd -= reserved_usd
            self.ledger.append(
                {
                    "label": label,
                    "reserved_usd": str(reserved_usd),
                    "actual_usd": "0",
                    "spent_usd": str(self.spent_usd),
                    "remaining_usd": str(self.remaining_usd),
                    "error": error,
                    "usage": {},
                }
            )


@dataclass(frozen=True)
class TransportResult:
    raw_text: str
    model_id: str
    provider: str
    usage: dict[str, Any]
    cost_usd: Decimal
    finish_reason: str | None = None


def estimate_call_cost(model_metadata: dict[str, Any], prompt_tokens: int, completion_tokens: int) -> Decimal:
    return (decimal_price(model_metadata, "prompt") * prompt_tokens) + (
        decimal_price(model_metadata, "completion") * completion_tokens
    )


def actual_cost_from_usage(model_metadata: dict[str, Any], usage: dict[str, Any], fallback: Decimal) -> Decimal:
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
        return estimate_call_cost(model_metadata, prompt_tokens, completion_tokens)
    return fallback


class OpenRouterTransport:
    def __init__(
        self,
        *,
        api_key: str,
        model_id: str,
        model_metadata: dict[str, Any],
        budget_gate: BudgetGate,
        max_prompt_tokens: int,
        max_completion_tokens: int,
        budget_completion_tokens: int | None = None,
        timeout_seconds: int = 60,
        prompt_language: str = "en",
        http_post: Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]] | None = None,
    ):
        if not api_key:
            raise PaidRunNotConfirmed("OPENROUTER_API_KEY is required for paid runs")
        self.api_key = api_key
        self.model_id = model_id
        self.model_metadata = model_metadata
        self.budget_gate = budget_gate
        self.max_prompt_tokens = max_prompt_tokens
        self.max_completion_tokens = max_completion_tokens
        self.budget_completion_tokens = budget_completion_tokens or max_completion_tokens
        self.timeout_seconds = timeout_seconds
        self.prompt_language = prompt_language
        self.http_post = http_post or self._post_json

    def complete_action(self, world: dict[str, Any], agent: dict[str, Any], cycle: int, arm: str) -> TransportResult:
        messages = build_messages(world, agent, cycle, arm, self.prompt_language)
        label = f"{self.model_id}:{world['world_id']}:{agent['agent_id']}:{cycle}:{arm}"
        reserved = self.budget_gate.reserve(
            estimate_call_cost(self.model_metadata, self.max_prompt_tokens, self.budget_completion_tokens),
            label=label,
        )
        body = {
            "model": self.model_id,
            "temperature": 0.2,
            "max_tokens": self.max_completion_tokens,
            "reasoning": {"exclude": True},
            "response_format": {"type": "json_object"},
            "messages": messages,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.environ.get("PUBLIC_SITE_URL", "https://local.tribe-v2.invalid"),
            "X-Title": "TRIBE v2 Synthetic Populations",
        }
        try:
            payload = self.http_post(OPENROUTER_CHAT_URL, headers, body)
        except Exception as exc:
            self.budget_gate.release(reserved, label, str(exc))
            raise

        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        actual_cost = actual_cost_from_usage(self.model_metadata, usage, reserved)
        self.budget_gate.commit(reserved, actual_cost, label=label, usage=usage)

        choice = payload.get("choices", [{}])[0]
        content = payload.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise OpenRouterError(
                "OpenRouter response missing message content: "
                f"model={payload.get('model')} "
                f"provider={payload.get('provider')} "
                f"finish_reason={choice.get('finish_reason')} "
                f"usage={usage}"
            )

        provider = payload.get("provider") or payload.get("model") or "openrouter"
        return TransportResult(
            raw_text=content,
            model_id=self.model_id,
            provider=str(provider),
            usage=usage,
            cost_usd=actual_cost,
            finish_reason=choice.get("finish_reason"),
        )

    def _post_json(self, url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OpenRouterError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
