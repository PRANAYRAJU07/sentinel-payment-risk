"""
Sentinel Risk Engine — Stub implementation for Phase 1.
Full implementation in Phase 7.
"""


class RiskEngine:
    """
    Stub risk engine.
    Returns is_ready=False until model is loaded in Phase 7.
    """
    _instance = None
    _ready = False

    def is_ready(self) -> bool:
        return self._ready


_risk_engine: RiskEngine | None = None


def get_risk_engine() -> RiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine
