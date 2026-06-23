#!/usr/bin/env python3
"""
AutoDev Studio - FastAPI Backend
Main entry point for the single API service managing automotive software
development projects, agents, and workflows.
"""
import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure backend directory is on path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("autodev")

# Shared application state for router access
from shared.state import set_service, app_state as _app_state


def init_services():
    """Initialize all backend service instances and register them in app state."""
    from agent_engine.manifest import ManifestReader
    from agent_engine.skill_loader import SkillLoader
    from agent_engine.output_stream import OutputStreamManager
    from agent_engine.agent_runtime import AgentRuntime
    from sdk_adapter.sdk_client import SDKClient
    from project_store.project_manager import ProjectManager
    from project_store.node_state import NodeStateManager

    # Paths (configurable via env vars)
    project_root = Path(os.environ.get(
        "AUTODEV_PROJECTS_ROOT",
        str(BASE_DIR.parent / "workspaces")
    ))
    project_root.mkdir(parents=True, exist_ok=True)

    reference_skills_dir = Path(os.environ.get(
        "AUTODEV_REFERENCE_SKILLS",
        str(BASE_DIR.parent / "skills")
    ))

    local_agents_dir = Path(os.environ.get(
        "AUTODEV_AGENTS_DIR",
        str(BASE_DIR.parent / "agents")
    ))

    # Look for manifest in multiple locations
    manifest_path = None
    env_manifest = os.environ.get("AUTODEV_MANIFEST_PATH", "")
    search_paths = []
    if env_manifest:
        search_paths.append(Path(env_manifest))
    search_paths.append(BASE_DIR.parent / "manifest" / "catalog.json")
    search_paths.append(BASE_DIR.parent / "manifest" / "agent_skill_manifest.json")

    for p in search_paths:
        if p.exists() and p.is_file():
            manifest_path = p
            break

    if manifest_path is None:
        # Search parent directories
        for parent in BASE_DIR.parents:
            candidate = parent / "manifest" / "agent_skill_manifest.json"
            if candidate.exists() and candidate.is_file():
                manifest_path = candidate
                break

    logger.info(f"Projects root:    {project_root}")
    logger.info(f"Reference skills: {reference_skills_dir}")
    logger.info(f"Local agents:     {local_agents_dir}")
    logger.info(f"Manifest path:    {manifest_path}")

    # Create service instances
    manifest = ManifestReader(str(manifest_path) if manifest_path else "")

    if manifest_path and manifest_path.exists():
        try:
            manifest.load()
            logger.info(f"Loaded manifest with {len(manifest.list_agents())} agents")
        except Exception as e:
            logger.warning(f"Failed to load manifest: {e}")
    else:
        logger.warning("Manifest not found. Routing/agent execution will be limited.")

    skill_loader = SkillLoader(
        reference_skills_dir=str(reference_skills_dir) if reference_skills_dir.exists() else None,
        agents_dir=str(local_agents_dir) if local_agents_dir.exists() else None,
    )

    output_stream = OutputStreamManager()

    sdk_client = SDKClient()

    node_state = NodeStateManager()

    project_manager = ProjectManager(str(project_root))

    # Audit logger (persists agent actions to project .autodev/audit.jsonl)
    from audit.audit_logger import AuditLogger
    audit_logger = AuditLogger(project_manager=project_manager)

    agent_runtime = AgentRuntime(
        manifest=manifest,
        skill_loader=skill_loader,
        sdk_client=sdk_client,
        output_stream=output_stream,
        node_state=node_state,
        audit_logger=audit_logger,
        project_manager=project_manager,
    )

    # AgentRouter — multi-factor weighted routing engine
    from agent_engine.agent_router import AgentRouter
    agent_router = AgentRouter(manifest=manifest)

    # Vector DB — knowledge base embedding index
    kb_root = Path(os.environ.get(
        "AUTODEV_KB_ROOT",
        str(BASE_DIR.parent / "knowledge-base")
    ))
    vector_db_path = Path(os.environ.get(
        "AUTODEV_VECTOR_DB_PATH",
        str(BASE_DIR / "data" / "vectors.db")
    ))
    vector_db_path.parent.mkdir(parents=True, exist_ok=True)

    from vector_store.vector_db import VectorDB
    vector_db = VectorDB(str(vector_db_path))
    vector_db.connect()

    # Pipeline — three-step routing + knowledge retrieval + execution
    from pipeline import Pipeline
    pipeline = Pipeline(
        agent_router=agent_router,
        vector_db=vector_db,
        kb_root=str(kb_root),
    )

    # Register all services in shared state
    set_service("manifest", manifest)
    set_service("skill_loader", skill_loader)
    set_service("output_stream", output_stream)
    set_service("sdk_client", sdk_client)
    set_service("node_state", node_state)
    set_service("agent_runtime", agent_runtime)
    set_service("agent_router", agent_router)
    set_service("project_manager", project_manager)
    set_service("audit_logger", audit_logger)
    set_service("pipeline", pipeline)
    set_service("vector_db", vector_db)

    logger.info("All services initialized successfully")
    return {
        "manifest": manifest,
        "skill_loader": skill_loader,
        "output_stream": output_stream,
        "sdk_client": sdk_client,
        "node_state": node_state,
        "agent_runtime": agent_runtime,
        "project_manager": project_manager,
        "audit_logger": audit_logger,
        "pipeline": pipeline,
        "vector_db": vector_db,
    }


def shutdown_services():
    """Cleanup on application shutdown."""
    logger.info("Shutting down services...")
    agent_runtime = _app_state.get("agent_runtime")
    if agent_runtime:
        running = agent_runtime.get_running_nodes()
        for node_id in running:
            logger.info(f"  Cancelling running agent: {node_id}")
    vector_db = _app_state.get("vector_db")
    if vector_db:
        try:
            vector_db.close()
        except Exception:
            pass
    pipeline_svc = _app_state.get("pipeline")
    if pipeline_svc and pipeline_svc._embedding_client:
        import asyncio as _asyncio
        try:
            _asyncio.get_event_loop().run_until_complete(
                pipeline_svc._embedding_client.close()
            )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("=" * 50)
    logger.info("  AutoDev Studio Backend Starting...")
    logger.info("=" * 50)

    # Startup
    services = init_services()

    # Prebuild vector store (async, non-blocking — fires and forgets)
    import asyncio as _asyncio
    from pipeline import prebuild_vector_store

    kb_root = services["pipeline"].kb_root
    db_path = services["vector_db"].db_path
    _asyncio.ensure_future(
        prebuild_vector_store(kb_root, db_path)
    )

    # Store service refs on app.state for convenience
    for key, value in services.items():
        setattr(app.state, key, value)

    yield

    # Shutdown
    shutdown_services()
    logger.info("  AutoDev Studio Backend Shutting down...")
    logger.info("=" * 50)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AutoDev Studio API",
        version="1.0.0",
        description="Backend service for automotive software development assistant",
        lifespan=lifespan,
    )

    # CORS - allow all origins for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from routers import project, agent, routing, file, websocket, audit
    from routers.pipeline import router as pipeline_router

    app.include_router(websocket.router)
    app.include_router(project.router)
    app.include_router(agent.router)
    app.include_router(routing.router)
    app.include_router(file.router)
    app.include_router(audit.router)
    app.include_router(pipeline_router)

    # Health check
    @app.get("/health")
    async def health_check():
        return JSONResponse({
            "status": "ok",
            "service": "autodev-studio-backend",
            "version": "1.0.0",
        })

    # API info
    @app.get("/")
    async def root():
        return {
            "name": "AutoDev Studio API",
            "version": "1.0.0",
            "endpoints": {
                "projects": "/projects",
                "agents": "/agent/list",
                "routing": "/routing/analyze",
                "pipeline": "/routing/pipeline/prepare",
                "files": "/files/list",
                "websocket": "/ws/{project_id}/{node_id}",
                "health": "/health",
            },
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("AUTODEV_PORT", "5090"))
    host = os.environ.get("AUTODEV_HOST", "127.0.0.1")

    logger.info(f"Starting AutoDev Studio on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
