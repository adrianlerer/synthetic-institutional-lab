"""Prompt construction for TRIBE v2 agent actions."""

from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT_EN = """You are an institutional-behavior agent inside a controlled synthetic population experiment.
Return only one JSON object. Do not include Markdown, prose, or extra keys.
Your output must use one action_category: comply, explore, evade, defect, abstain.
Keep evade separate from explore: evade means formal acknowledgment with loophole or hidden workaround.
Do not choose a category because the experiment mentions it. Choose the action the agent would take under the rules and incentives."""

SYSTEM_PROMPT_ES = """Eres un agente de comportamiento institucional dentro de un experimento controlado de poblaciones sinteticas.
Devuelve solo un objeto JSON. No incluyas Markdown, prosa ni claves extra.
Tu salida debe usar una action_category: comply, explore, evade, defect, abstain.
Mantene evade separado de explore: evade significa reconocimiento formal con loophole, excepcion, estrategia oculta o workaround no monitoreado.
No elijas una categoria porque el experimento la menciona. Elegi la accion que el agente tomaria bajo las reglas e incentivos."""

SYSTEM_PROMPTS = {
    "en": SYSTEM_PROMPT_EN,
    "es": SYSTEM_PROMPT_ES,
}


def compact_world_for_prompt(world: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "world_id": world["world_id"],
        "cli_level": world["cli_level"],
        "cli_features": world["cli_features"],
        "ruleset": world["ruleset"],
        "palimpsest_layers": world.get("palimpsest_layers", []),
        "resources": world["resources"],
        "institutions": world["institutions"],
        "communication_topology": world["communication_topology"],
        "world_version": world.get("world_version", "unknown"),
        "recent_history": world["history"][-3:],
    }
    for optional_field in ("experiment", "treatments"):
        if optional_field in world:
            compact[optional_field] = world[optional_field]
    if "political_economy" in world:
        state = world["political_economy"]
        observable_fields = (
            "automation_intensity",
            "capital_concentration",
            "labor_share",
            "revolt_pressure",
            "redistribution_burden",
            "repression_burden",
            "coercive_infrastructure",
            "institutional_lock_in",
        )
        compact["political_economy"] = {
            field: state[field] for field in observable_fields if field in state
        }
    return compact


def build_user_prompt(world: dict[str, Any], agent: dict[str, Any], cycle: int, arm: str, language: str = "en") -> str:
    schema = {
        "agent_id": agent["agent_id"],
        "cycle": cycle,
        "arm": arm,
        "declared_intent": "one of comply, explore, evade, defect, abstain",
        "action": "short action verb phrase",
        "action_category": "one of comply, explore, evade, defect, abstain",
        "rule_references": ["rule ids referenced"],
        "resource_move": None if arm == "normative_reform" else {"claim": "number or short move"},
        "justification": "one short reason",
        "confidence": "number from 0 to 1",
    }
    if world.get("experiment") == "automation_repression_causal":
        schema.update(
            {
                "policy_choice": "one of regulate_automation, redistribute, repress, adjudicate, abstain",
                "revolt_choice": "one of participate, do_not_participate, not_applicable",
                "labor_share_assessment": "number from 0 to 1",
                "revolt_pressure_assessment": "number from 0 to 1",
                "coercive_infrastructure_reliance": "number from 0 to 1",
                "normative_layer": "one palimpsest layer id",
            }
        )
    payload = {
        "language_condition": language,
        "instruction_language": (
            "Write string values in English while preserving JSON keys and action category labels exactly."
            if language == "en"
            else "Escribi los valores de texto en espanol, pero conserva exactamente las claves JSON y las etiquetas de action_category."
        ),
        "task": (
            "Choose the agent's next institutional action and complete every political-economy measurement field."
            if world.get("experiment") == "automation_repression_causal"
            else "Choose the agent's next institutional action."
        ),
        "action_definitions": {
            "comply": "follow the active rule or implement the reform substantively",
            "explore": "negotiate, seek adjudication, propose amendment, or search for a lawful clarification",
            "evade": "formally acknowledge the rule while using a loophole, exception, hidden timing, or unmonitored workaround",
            "defect": "openly violate, block, sabotage, or ignore the rule",
            "abstain": "refuse to act, wait, or exit",
        },
        "cycle": cycle,
        "arm": arm,
        "agent": agent,
        "world": compact_world_for_prompt(world),
        "required_json_schema_example": schema,
    }
    if world.get("experiment") == "automation_repression_causal":
        payload["policy_definitions"] = {
            "regulate_automation": "reduce or delay automation intensity",
            "redistribute": "use transfers or public goods to address distributive conflict",
            "repress": "use coercive controls to deter political coordination",
            "adjudicate": "seek an institutional ruling without selecting another policy",
            "abstain": "take no institutional policy action",
        }
        payload["role_rule"] = (
            "Only the capitalist_state selects policy_choice; other roles use abstain. "
            "Only the worker_coalition selects revolt_choice; other roles use not_applicable."
        )
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)


def build_messages(
    world: dict[str, Any],
    agent: dict[str, Any],
    cycle: int,
    arm: str,
    language: str = "en",
) -> list[dict[str, str]]:
    if language not in SYSTEM_PROMPTS:
        raise ValueError(f"unsupported prompt language: {language}")
    return [
        {"role": "system", "content": SYSTEM_PROMPTS[language]},
        {"role": "user", "content": build_user_prompt(world, agent, cycle, arm, language)},
    ]
