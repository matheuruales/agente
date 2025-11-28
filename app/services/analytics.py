"""
Lightweight in-memory analytics for processed leads.
Keeps counters for lead_score, urgencia, tipo_propiedad, canal y zonas.
"""

from collections import Counter
from threading import Lock
from typing import Any, Dict, List, Optional


class _AnalyticsStore:
    def __init__(self) -> None:
        self.total_leads = 0
        self.lead_score_counts: Counter[str] = Counter()
        self.urgency_counts: Counter[str] = Counter()
        self.property_counts: Counter[str] = Counter()
        self.channel_counts: Counter[str] = Counter()
        self.zone_counts: Counter[str] = Counter()
        self._budget_sum = 0
        self._budget_count = 0
        self._lock = Lock()

    def record(self, *, lead_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Store the outcome of a lead analysis for analytics purposes.
        """
        with self._lock:
            self.total_leads += 1
            score = (result.get("lead_score") or "C").upper()
            self.lead_score_counts[score] += 1

            urg = (result.get("urgencia") or "media").lower()
            self.urgency_counts[urg] += 1

            tprop = result.get("tipo_propiedad") or "desconocido"
            self.property_counts[str(tprop)] += 1

            canal = (lead_data.get("canal") or "desconocido").lower()
            self.channel_counts[canal] += 1

            zona = result.get("zona")
            if zona:
                self.zone_counts[str(zona)] += 1

            presupuesto = result.get("presupuesto")
            if isinstance(presupuesto, (int, float)):
                self._budget_sum += int(presupuesto)
                self._budget_count += 1

    def summary(self) -> Dict[str, Any]:
        """
        Return a snapshot of the current analytics summary.
        """
        with self._lock:
            avg_budget: Optional[int] = None
            if self._budget_count:
                avg_budget = int(self._budget_sum / self._budget_count)

            def _top(counter: Counter[str], limit: int = 5) -> List[Dict[str, Any]]:
                return [{"zona": name, "count": count} for name, count in counter.most_common(limit)]

            return {
                "total_leads": self.total_leads,
                "lead_score_counts": dict(self.lead_score_counts),
                "urgency_counts": dict(self.urgency_counts),
                "tipo_propiedad_counts": dict(self.property_counts),
                "canal_counts": dict(self.channel_counts),
                "avg_presupuesto": avg_budget,
                "top_zonas": _top(self.zone_counts),
            }


_store = _AnalyticsStore()


def record_lead_event(lead_data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Public helper to record analytics event.
    """
    _store.record(lead_data=lead_data, result=result)


def get_analytics_summary() -> Dict[str, Any]:
    """
    Retrieve current analytics summary.
    """
    return _store.summary()
