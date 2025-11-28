"""
Pydantic schemas for the lead analysis API.
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class LeadRequest(BaseModel):
    mensaje: str = Field(..., description="Mensaje o texto libre del lead.")
    canal: Optional[str] = Field(None, description="Origen del lead: web, whatsapp, telegram, etc.")
    nombre: Optional[str] = Field(None, description="Nombre de la persona.")
    contacto: Optional[str] = Field(None, description="Datos de contacto: email o whatsapp.")


class LeadResponse(BaseModel):
    lead_score: Literal["A", "B", "C"] = Field(..., description="Clasificación del lead.")
    presupuesto: Optional[int] = Field(
        None, description="Presupuesto en moneda local sin símbolos, o null."
    )
    zona: Optional[str] = Field(None, description="Ciudad o zona indicada, o null.")
    tipo_propiedad: Optional[Literal["apartamento", "casa", "local", "lote", "otro"]] = Field(
        None, description="Tipo de propiedad normalizado."
    )
    urgencia: Literal["alta", "media", "baja"] = Field(..., description="Nivel de urgencia.")
    razonamiento: str = Field(..., description="Breve explicación del score.")


class TopZona(BaseModel):
    zona: str
    count: int


class AnalyticsSummary(BaseModel):
    total_leads: int
    lead_score_counts: Dict[str, int]
    urgency_counts: Dict[str, int]
    tipo_propiedad_counts: Dict[str, int]
    canal_counts: Dict[str, int]
    avg_presupuesto: Optional[int]
    top_zonas: List[TopZona]
