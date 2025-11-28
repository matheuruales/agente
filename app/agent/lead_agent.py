"""
Lead analysis agent that uses LangChain + LLM to classify real-estate leads.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None  # type: ignore

from .prompts import BASE_PROMPT
from app.services.scoring import apply_rule_based_score

load_dotenv()

MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))


def _load_llm() -> Optional["ChatOpenAI"]:
    """
    Configure ChatOpenAI using environment variables; the OpenAI client
    reads OPENAI_API_KEY from the environment by default.
    """
    if ChatOpenAI is None:
        return None
    try:
        return ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    except Exception:
        return None


llm = _load_llm()


DEFAULT_RESPONSE: Dict[str, Any] = {
    "presupuesto": None,
    "zona": None,
    "tipo_propiedad": None,
    "urgencia": "media",
    "lead_score": "C",
    "razonamiento": "No se pudo interpretar bien el mensaje",
}


def _parse_json_response(content: str) -> Dict[str, Any]:
    """
    Attempt to parse the LLM response as JSON; tolerate fenced code blocks.
    """
    cleaned = content.strip()

    # Remove Markdown code fences if present.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # After stripping backticks, there may be language hints like json\n{...}
        fence_index = cleaned.find("{")
        if fence_index != -1:
            cleaned = cleaned[fence_index:]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        return DEFAULT_RESPONSE.copy()


def _normalize_presupuesto(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else None
    return None


def _normalize_tipo_propiedad(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, str):
        v = value.strip().lower()
        if not v:
            return None
        if v in {"apartamento", "apto", "departamento", "dept", "dept.", "apartment"}:
            return "apartamento"
        if v in {"casa", "house"}:
            return "casa"
        if v in {"local", "local comercial", "comercial"}:
            return "local"
        if v in {"lote", "terreno", "parcela"}:
            return "lote"
        if v in {"otro", "otros", "other"}:
            return "otro"
        return "otro"

    return None


def _normalize_urgencia(value: Any) -> str:
    if isinstance(value, str):
        urg = value.strip().lower()
    else:
        urg = "media"

    if urg not in {"alta", "media", "baja"}:
        return "media"
    return urg


def _normalize_lead_score(value: Any) -> str:
    score = str(value).upper() if value is not None else "C"
    if score not in {"A", "B", "C"}:
        score = "C"
    return score


def _normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return str(value)


def _normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "presupuesto": _normalize_presupuesto(data.get("presupuesto")),
        "zona": _normalize_text(data.get("zona")),
        "tipo_propiedad": _normalize_tipo_propiedad(data.get("tipo_propiedad")),
        "urgencia": _normalize_urgencia(data.get("urgencia")),
        "lead_score": _normalize_lead_score(data.get("lead_score")),
        "razonamiento": _normalize_text(data.get("razonamiento"))
        or "Sin razonamiento proporcionado",
    }

    # Apply simple rule-based scoring adjustments as a safety net.
    normalized["lead_score"] = apply_rule_based_score(
        lead_score=normalized["lead_score"],
        presupuesto=normalized["presupuesto"],
        zona=normalized["zona"],
        tipo_propiedad=normalized["tipo_propiedad"],
        urgencia=normalized["urgencia"],
    )

    return normalized


def analyze_lead_message(message: str) -> Dict[str, Any]:
    """
    Analyze the lead message using the LLM and normalize the response.
    """
    if llm is None:
        fallback = DEFAULT_RESPONSE.copy()
        fallback["razonamiento"] = "LLM no disponible (clave o dependencia faltante)"
        return fallback

    prompt = BASE_PROMPT.replace("{mensaje}", message)

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
    except Exception:
        return DEFAULT_RESPONSE.copy()

    parsed = _parse_json_response(content)
    return _normalize_payload(parsed)
