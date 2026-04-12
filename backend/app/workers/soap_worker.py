from app.schemas.sessions import SoapSummary


def generate_soap() -> SoapSummary:
    return SoapSummary(
        subjective="Patient describes symptoms.",
        objective="Observation pending.",
        assessment="Assessment pending.",
        plan="Plan pending.",
    )
