"""
Audit trail REST endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from shared.state import get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


def _get_audit_logger():
    al = get_service("audit_logger")
    if al is None:
        raise HTTPException(status_code=500, detail="Audit logger not initialized")
    return al


@router.get("/{project_id}")
async def get_audit_trail(
    project_id: str,
    node_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    time_from: Optional[str] = Query(None),
    time_to: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Get filtered audit trail for a project.
    Supports filtering by node_id, event_type (comma-separated), time range.
    """
    audit_logger = _get_audit_logger()

    event_types = None
    if event_type:
        event_types = [t.strip() for t in event_type.split(",") if t.strip()]

    events = await audit_logger.get_audit_trail(
        project_id=project_id,
        node_id=node_id,
        event_types=event_types,
        time_from=time_from,
        time_to=time_to,
        limit=limit,
        offset=offset,
    )

    return {
        "project_id": project_id,
        "events": events,
        "count": len(events),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{project_id}/nodes/{node_id}")
async def get_node_audit(
    project_id: str,
    node_id: str,
    limit: int = Query(200, ge=1, le=1000),
):
    """Get audit trail for a specific node."""
    audit_logger = _get_audit_logger()
    events = await audit_logger.get_node_audit(project_id, node_id, limit=limit)
    return {
        "project_id": project_id,
        "node_id": node_id,
        "events": events,
        "count": len(events),
    }


@router.get("/{project_id}/summary")
async def get_audit_summary(project_id: str):
    """Get summary statistics for a project's audit trail."""
    audit_logger = _get_audit_logger()
    return await audit_logger.get_summary(project_id)
