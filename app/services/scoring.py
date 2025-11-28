"""
Rule-based scoring helpers to complement the LLM response.
"""

from typing import Optional


def apply_rule_based_score(
    *,
    lead_score: Optional[str],
    presupuesto: Optional[int],
    zona: Optional[str],
    tipo_propiedad: Optional[str],
    urgencia: str,
) -> str:
    """
    Validate and, if needed, adjust the lead_score with lightweight heuristics.
    """
    normalized_score = (lead_score or "C").upper()
    if normalized_score not in {"A", "B", "C"}:
        normalized_score = "C"

    has_budget = presupuesto is not None
    has_location = bool(zona)
    has_property_type = bool(tipo_propiedad)
    high_intent = urgencia == "alta"
    medium_intent = urgencia == "media"

    if (has_budget and (has_location or has_property_type)) and (high_intent or medium_intent):
        return "A"

    if (has_budget and medium_intent) or (has_property_type and medium_intent):
        return "B"

    if normalized_score == "A" and not has_budget and not has_location:
        return "B"

    if normalized_score == "B" and urgencia == "baja":
        return "C"

    if has_budget or has_property_type or has_location:
        return normalized_score if normalized_score in {"A", "B"} else "B"

    return normalized_score
