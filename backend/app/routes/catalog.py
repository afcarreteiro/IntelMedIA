from fastapi import APIRouter

from app.config import settings
from app.services.catalog import SUPPORTED_LANGUAGES


router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/languages")
async def get_languages():
    return {
        "region": settings.region,
        "languages": SUPPORTED_LANGUAGES,
        "transcript_retention": settings.transcript_retention,
    }
