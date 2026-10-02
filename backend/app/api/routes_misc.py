"""Miscellaneous endpoints: registry lookup, privacy disclosures, and resources."""

from typing import Any, Dict
from fastapi import APIRouter, Query
from app.modules.registry.service import get_registry_service

router = APIRouter(prefix="/v1", tags=["Registry & Info"])


@router.get("/registry/lookup")
async def registry_lookup(
    q: str = Query(..., min_length=1, max_length=200, description="Registration number or entity name to look up"),
) -> Dict[str, Any]:
    """Offline dated SEBI intermediary snapshot lookup.

    HONEST DISCLOSURE:
    - Queries a dated, local offline snapshot, not live SEBI systems.
    - If not found, status is 'not_found_in_snapshot' ('could not confirm in our snapshot'), never 'fake'.
    """
    service = get_registry_service()
    return service.lookup(q)
