"""
Project CRUD and node tree management router.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid
from datetime import datetime
import logging

from shared.models import (
    Project, AgentNode, NodeStatus,
    CreateProjectRequest, AddNodeRequest,
)
from shared.state import get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_project_mgr():
    mgr = get_service("project_manager")
    if mgr is None:
        raise HTTPException(status_code=500, detail="Project manager not initialized")
    return mgr


def _get_node_state():
    mgr = get_service("node_state")
    if mgr is None:
        raise HTTPException(status_code=500, detail="Node state manager not initialized")
    return mgr


@router.post("", response_model=Project)
async def create_project(req: CreateProjectRequest):
    """Create a new project with a local directory."""
    try:
        project_mgr = _get_project_mgr()
        project = project_mgr.create_project(req.name)
        return project
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[Project])
async def list_projects():
    """List all known projects."""
    project_mgr = _get_project_mgr()
    return project_mgr.list_projects()


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project details."""
    project_mgr = _get_project_mgr()
    project = project_mgr.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    project_mgr = _get_project_mgr()
    ok = project_mgr.delete_project(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}


@router.post("/{project_id}/nodes", response_model=AgentNode)
async def add_node(project_id: str, req: AddNodeRequest):
    """Add an agent node to a project."""
    project_mgr = _get_project_mgr()
    node_state = _get_node_state()

    project = project_mgr.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    node = AgentNode(
        id=f"node-{uuid.uuid4().hex[:8]}",
        agent_name=req.agent_name,
        domain=req.domain,
        status=NodeStatus.PENDING,
        workflow_steps=req.workflow_steps or [],
        total_steps=len(req.workflow_steps or []),
        deliverables=[],
        context_files=req.context_files or [],
        created_at=datetime.utcnow().isoformat(),
    )

    result = project_mgr.add_node(project_id, node)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to add node")

    node_state.register(node.id, NodeStatus.PENDING)

    # Audit: node created
    audit_logger = get_service("audit_logger")
    if audit_logger:
        import asyncio
        from shared.models import AuditEventType
        asyncio.ensure_future(audit_logger.log_event(
            project_id=project_id,
            node_id=node.id,
            event_type=AuditEventType.NODE_CREATED,
            data={"agent_name": req.agent_name, "domain": req.domain},
            actor="user",
        ))

    return node


@router.put("/{project_id}/nodes/{node_id}", response_model=AgentNode)
async def update_node(project_id: str, node_id: str, updates: Dict[str, Any]):
    """Update a node's properties."""
    project_mgr = _get_project_mgr()

    project = project_mgr.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updated = project_mgr.update_node(project_id, node_id, **updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return updated


@router.delete("/{project_id}/nodes/{node_id}")
async def remove_node(project_id: str, node_id: str):
    """Remove a node from a project."""
    project_mgr = _get_project_mgr()
    node_state = _get_node_state()

    project = project_mgr.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ok = project_mgr.remove_node(project_id, node_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Node not found")

    node_state.remove(node_id)
    return {"status": "removed"}
