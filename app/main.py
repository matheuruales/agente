"""
FastAPI app exposing the lead analysis endpoint.
"""

from fastapi import FastAPI, HTTPException

from app.agent.lead_agent import analyze_lead_message
from app.schemas import AnalyticsSummary, LeadRequest, LeadResponse
from app.services.analytics import get_analytics_summary, record_lead_event

app = FastAPI(
    title="Lead Scoring Agent API",
    description="Agente IA para calificar leads inmobiliarios (A/B/C).",
    version="1.0.0",
)


@app.post("/api/lead/analyze", response_model=LeadResponse)
async def analyze_lead(lead: LeadRequest) -> LeadResponse:
    try:
        result = analyze_lead_message(lead.mensaje)
    except Exception as exc:  # Defensive: unexpected runtime issues.
        raise HTTPException(status_code=500, detail="Error interno del agente") from exc

    # Registrar evento para analítica ligera
    record_lead_event(lead.dict(), result)

    return LeadResponse(
        lead_score=result.get("lead_score"),
        presupuesto=result.get("presupuesto"),
        zona=result.get("zona"),
        tipo_propiedad=result.get("tipo_propiedad"),
        urgencia=result.get("urgencia"),
        razonamiento=result.get("razonamiento"),
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/analytics/summary", response_model=AnalyticsSummary)
async def analytics_summary() -> AnalyticsSummary:
    return AnalyticsSummary(**get_analytics_summary())
