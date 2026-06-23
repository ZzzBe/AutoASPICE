"""
Pipeline router — three-step pipeline endpoints.

POST /routing/pipeline/prepare  — Route task + retrieve knowledge (Steps 1-2)
POST /routing/pipeline/execute  — Execute agent with augmented context (Step 3)
GET  /routing/pipeline/status   — Check if pipeline services are ready
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException

from shared.models import (
    RoutingRequestEnhanced,
    ExecuteAgentRequest,
    LLMConfigRequest,
)
from shared.state import get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routing/pipeline", tags=["pipeline"])


def _get_pipeline():
    """Get the Pipeline service."""
    pipeline = get_service("pipeline")
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline service not available")
    return pipeline


@router.post("/prepare")
async def prepare_pipeline(req: RoutingRequestEnhanced):
    """
    Steps 1-2: Route the task and retrieve relevant knowledge.

    Request body:
      - text_instruction: Task description
      - uploaded_files: File names for context
      - file_contents: File content map
      - llm_config: Optional LLM config for fine-ranking

    Returns:
      - suggestions: Ranked agent suggestions with confidence scores
      - knowledge_chunks: Relevant knowledge base excerpts
      - knowledge_summary: Human-readable knowledge summary
      - detected_domains: Detected automotive domains
      - fan_out_plan: Multi-agent dispatch plan (if applicable)
    """
    pipeline = _get_pipeline()

    try:
        result = await pipeline.prepare(
            text_instruction=req.text_instruction,
            llm_config=req.llm_config,
            uploaded_files=req.uploaded_files,
            file_contents=req.file_contents,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Pipeline prepare failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_pipeline(req: dict):
    """
    Step 3: Execute the selected agent with augmented context.

    Request body:
      - project_id: Target project
      - node_id: Target node
      - agent_name: Selected agent (from prepare step)
      - user_instruction: Task description / user input
      - llm_config: LLM configuration
      - knowledge_chunks: Knowledge chunks from prepare step (optional)
      - context_files: Additional context file paths

    The agent begins executing immediately via WebSocket streaming.
    """
    pipeline = _get_pipeline()

    try:
        result = await pipeline.execute(
            project_id=req.get("project_id", ""),
            node_id=req.get("node_id", ""),
            agent_name=req.get("agent_name", ""),
            user_instruction=req.get("user_instruction", ""),
            llm_config=req.get("llm_config"),
            knowledge_chunks=req.get("knowledge_chunks"),
            context_files=req.get("context_files", []),
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline execute failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def pipeline_status():
    """Check if pipeline services (vector DB, agent router) are ready."""
    pipeline = get_service("pipeline")
    router_svc = get_service("agent_router")

    status = {
        "pipeline": "ready" if pipeline else "not_available",
        "agent_router": "ready" if router_svc else "not_available",
    }

    if pipeline and pipeline.vector_db:
        try:
            pipeline.vector_db.connect()
            stats = pipeline.vector_db.get_stats()
            pipeline.vector_db.close()
            status["vector_db"] = {
                "ready": True,
                "total_chunks": stats["total_chunks"],
                "categories": stats["categories"],
            }
        except Exception:
            status["vector_db"] = {"ready": False}

    return status
