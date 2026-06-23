"""
Agent execution router - start, stop, status, checkpoint management.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
import os
from pathlib import Path

from shared.models import ExecuteAgentRequest, NodeStatus
from shared.state import get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agents"])

# Local cache directories
_LOCAL_AGENTS_ROOT = Path(__file__).resolve().parent.parent.parent / "agents"
_LOCAL_SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent / "skills"


def _local_agent_path(agent_file: str) -> str | None:
    """Map manifest agent_file to local cache path. Return path if exists, else None."""
    if not agent_file:
        return None
    fname = os.path.basename(agent_file)
    # Search all subdirs
    for root, _, files in os.walk(_LOCAL_AGENTS_ROOT):
        if fname in files:
            return os.path.join(root, fname)
    return None

def _local_skill_path(skill_path: str) -> str | None:
    """Map manifest skill path to local cache. Return path if exists, else None."""
    if not skill_path:
        return None
    fname = os.path.basename(skill_path)
    for root, _, files in os.walk(_LOCAL_SKILLS_ROOT):
        if fname in files:
            return os.path.join(root, fname)
    return None

_LOCAL_WORKFLOWS_ROOT = Path(__file__).resolve().parent.parent.parent / "workflows"

def _local_workflow_path(wf_path: str) -> str | None:
    """Map manifest workflow path to local cache."""
    if not wf_path:
        return None
    fname = os.path.basename(wf_path)
    # Also check by relative path within workflows/
    if _LOCAL_WORKFLOWS_ROOT.exists():
        for root, _, files in os.walk(_LOCAL_WORKFLOWS_ROOT):
            if fname in files:
                return os.path.join(root, fname)
    return None


def _get_manifest():
    m = get_service("manifest")
    if m is None:
        raise HTTPException(status_code=500, detail="Manifest not initialized")
    return m


def _get_agent_runtime():
    rt = get_service("agent_runtime")
    if rt is None:
        raise HTTPException(status_code=500, detail="Agent runtime not initialized")
    return rt


def _get_node_state():
    ns = get_service("node_state")
    if ns is None:
        raise HTTPException(status_code=500, detail="Node state manager not initialized")
    return ns


@router.post("/execute")
async def execute_agent(req: ExecuteAgentRequest):
    """Start agent execution as a background task."""
    manifest = _get_manifest()
    agent_runtime = _get_agent_runtime()

    # Validate the agent exists
    agent_info = manifest.get_agent(req.agent_name)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_name}' not found")

    # Check if already running
    if agent_runtime.is_running(req.node_id):
        raise HTTPException(status_code=409, detail="Agent is already running")

    # Get workflow steps from the YAML converter
    from sdk_adapter.yaml_converter import YAMLConverter
    converter = YAMLConverter()

    # Build workflow steps from agent config
    agent_domain = manifest.get_agent_domain(req.agent_name)
    agent_config = {
        "name": req.agent_name,
        "domain": agent_domain,
        "capabilities": manifest.get_agent_capabilities(req.agent_name),
    }
    workflow_steps = converter.agent_config_to_workflow_steps(agent_config)

    # Submit to runtime (background task)
    agent_runtime.submit_task(req, workflow_steps)

    return {
        "status": "started",
        "node_id": req.node_id,
        "agent_name": req.agent_name,
        "steps": len(workflow_steps),
    }


@router.post("/stop/{node_id}")
async def stop_agent(node_id: str):
    """Stop a running agent."""
    agent_runtime = _get_agent_runtime()
    stopped = await agent_runtime.stop_agent(node_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="Agent not running or not found")
    return {"status": "stopped", "node_id": node_id}


@router.get("/status/{node_id}")
async def get_agent_status(node_id: str):
    """Get the current execution status of an agent."""
    agent_runtime = _get_agent_runtime()
    node_state = _get_node_state()

    status = node_state.get_status(node_id)
    checkpoint_state = agent_runtime.checkpoint_mgr.get_state_snapshot(node_id)

    return {
        "node_id": node_id,
        "status": status.value if status else "unknown",
        "current_step": checkpoint_state.get("current_step", 0),
        "total_steps": checkpoint_state.get("total_steps", 0),
        "is_paused": checkpoint_state.get("is_paused", False),
        "chat_history": [],  # chat history is async-only; use checkpoint/chat endpoint
    }


@router.post("/checkpoint/{node_id}/continue")
async def checkpoint_continue(node_id: str):
    """Continue execution from a checkpoint pause."""
    agent_runtime = _get_agent_runtime()
    continued = await agent_runtime.continue_from_checkpoint(node_id)
    if not continued:
        raise HTTPException(status_code=400, detail="Agent is not at a checkpoint")
    return {"status": "continued", "node_id": node_id}


@router.post("/checkpoint/{node_id}/chat")
async def checkpoint_chat(node_id: str, message: Dict[str, str]):
    """Send a chat message to the agent at a checkpoint."""
    agent_runtime = _get_agent_runtime()
    text = message.get("message", "")
    if not text:
        raise HTTPException(status_code=400, detail="Message is required")

    # Audit: checkpoint chat
    audit_logger = get_service("audit_logger")
    if audit_logger:
        import asyncio as _asyncio
        from shared.models import AuditEventType
        _asyncio.ensure_future(audit_logger.log_event(
            project_id="", node_id=node_id,
            event_type=AuditEventType.CHECKPOINT_CHAT,
            data={"message": text[:500]},
            actor="user",
        ))

    response = await agent_runtime.chat_at_checkpoint(node_id, text)
    return response


@router.post("/checkpoint/{node_id}/approve")
async def checkpoint_approve(node_id: str, body: Dict[str, Any] = None):
    """Approve the current checkpoint and resume execution."""
    agent_runtime = _get_agent_runtime()
    body = body or {}
    reason = body.get("reason", "")

    result = await agent_runtime.checkpoint_mgr.approve(
        node_id, decided_by="user", reason=reason
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "approved", "node_id": node_id, "decision": result}


@router.post("/checkpoint/{node_id}/reject")
async def checkpoint_reject(node_id: str, body: Dict[str, Any] = None):
    """
    Reject the current checkpoint and stop the agent.
    Body: { reason: str, action: "stop"|"retry" }
    """
    agent_runtime = _get_agent_runtime()
    body = body or {}
    reason = body.get("reason", "")

    result = await agent_runtime.checkpoint_mgr.reject(
        node_id, decided_by="user", reason=reason
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "rejected", "node_id": node_id, "decision": result}


@router.post("/install")
async def install_agent_to_project(req: dict):
    """
    Install an agent + its skills into a project workspace.
    Body: { agent_name, project_id }
    Copies agent YAML and all required skill YAMLs to the project directory.
    """
    manifest = _get_manifest()
    project_mgr = get_service("project_manager")
    skill_loader = get_service("skill_loader")

    agent_name = req.get("agent_name", "")
    project_id = req.get("project_id", "")

    if not agent_name or not project_id:
        raise HTTPException(status_code=400, detail="agent_name and project_id are required")

    project = project_mgr.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = skill_loader.install_agent_to_workspace(
        workspace_root=project.root_path,
        agent_name=agent_name,
        manifest=manifest,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/download")
async def download_from_github(req: dict):
    """
    Download agent YAML + skills YAMLs + workflow YAMLs from GitHub raw URLs
    and save to local cache directories.
    Body: { agent_name }
    """
    manifest = _get_manifest()
    agent_name = req.get("agent_name", "")
    if not agent_name:
        raise HTTPException(status_code=400, detail="agent_name is required")

    agent_info = manifest.get_agent(agent_name)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    import httpx, shutil
    domain = agent_info.get("domain", "unknown")
    results = {"agent_name": agent_name, "downloaded": [], "errors": []}

    async def _fetch_save(url: str, dest: str):
        """Fetch a file from URL and save to destination."""
        if not url:
            return False
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(r.content)
                    return True
                else:
                    results["errors"].append(f"HTTP {r.status_code} from {url}")
        except Exception as e:
            results["errors"].append(f"Download error from {url}: {e}")
        return False

    # 1) Download agent YAML
    agent_url = agent_info.get("github_url", "")
    agent_fname = os.path.basename(agent_info.get("agent_file", "")) or f"{agent_name}.yaml"
    agent_dest = os.path.join(_LOCAL_AGENTS_ROOT, domain, agent_fname)
    agent_ok = await _fetch_save(agent_url, agent_dest)

    # 2) Download skills
    skills_done = 0
    skill_paths = manifest.get_agent_skills(agent_name)
    for sp in (skill_paths or []):
        sp_str = sp.get("path", "") if isinstance(sp, dict) else str(sp)
        sk_name = sp.get("name", "") if isinstance(sp, dict) else ""
        if not sp_str:
            continue
        # Get skill github_url from the skill_index
        sk_info = manifest._data.get("skill_index", {}).get(sk_name, {})
        sk_url = sk_info.get("github_url", "") if isinstance(sk_info, dict) else ""
        if not sk_url:
            # Fallback: derive from agent's github_url repo root
            # agent_url: .../main/agents/domain/file.yaml
            # Strip all segments from the agent_file path to reach repo root
            agent_file = agent_info.get("agent_file", "")
            file_depth = len(os.path.normpath(agent_file).split(os.sep))
            sk_url = agent_url.rsplit("/", file_depth)[0] + "/" + sp_str if agent_url else ""

        rel_dir = os.path.dirname(sp_str.replace("skills/", "", 1))
        sk_dest = os.path.join(str(_LOCAL_SKILLS_ROOT), rel_dir, os.path.basename(sp_str))
        if await _fetch_save(sk_url, sk_dest):
            skills_done += 1

    # 3) Download workflows matching this agent's domain
    wfs_done = 0
    all_wfs = manifest._data.get("workflows", {})
    for wf_name, wf_info in all_wfs.items():
        if not isinstance(wf_info, dict):
            continue
        wf_domain = wf_info.get("domain", "")
        if wf_domain != domain and domain not in wf_domain and wf_domain not in domain:
            continue
        wf_url = wf_info.get("github_url", "")
        wf_path = wf_info.get("path", "")
        if not wf_url or not wf_path:
            continue
        wf_dest_dir = os.path.join(str(_LOCAL_WORKFLOWS_ROOT), wf_domain)
        wf_dest = os.path.join(wf_dest_dir, os.path.basename(wf_path))
        if await _fetch_save(wf_url, wf_dest):
            wfs_done += 1

    _invalidate_domain_cache()   # installed status changed
    return {
        "agent_name": agent_name,
        "domain": domain,
        "agent_downloaded": agent_ok,
        "skills_downloaded": skills_done,
        "skills_total": len(skill_paths or []),
        "workflows_downloaded": wfs_done,
        "errors": results["errors"] if results["errors"] else None,
    }


@router.post("/install-to-cache")
async def install_agent_to_cache(req: dict):
    """
    Download agent + skills from reference repos into local cache dirs.
    Body: { agent_name }
    """
    manifest = _get_manifest()
    skill_loader = get_service("skill_loader")

    agent_name = req.get("agent_name", "")
    if not agent_name:
        raise HTTPException(status_code=400, detail="agent_name is required")

    agent_info = manifest.get_agent(agent_name)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    # Copy agent YAML to local agents/<domain>/ dir
    domain = agent_info.get("domain", "unknown")
    agent_file = agent_info.get("agent_file", "")
    fname = os.path.basename(agent_file) if agent_file else f"{agent_name}.yaml"
    dst_agent_dir = _LOCAL_AGENTS_ROOT / domain
    dst_agent_dir.mkdir(parents=True, exist_ok=True)

    installed = False
    # Try reference repos
    for ref_root in _get_ref_roots():
        src = os.path.join(ref_root, agent_file) if agent_file else None
        if src and os.path.isfile(src):
            import shutil
            shutil.copy2(src, str(dst_agent_dir / fname))
            installed = True
            break

    # Copy skills too
    import shutil
    skills_copied = 0
    skill_paths = manifest.get_agent_skills(agent_name)
    for sp in (skill_paths or []):
        sp_str = sp.get("path", "") if isinstance(sp, dict) else str(sp)
        if not sp_str:
            continue
        sfname = os.path.basename(sp_str)
        rel_dir = os.path.dirname(sp_str.replace("skills/", "", 1))
        dst_skill_dir = _LOCAL_SKILLS_ROOT / rel_dir
        dst_skill_dir.mkdir(parents=True, exist_ok=True)
        for ref_root in _get_ref_roots():
            src_skill = os.path.join(ref_root, sp_str)
            if os.path.isfile(src_skill):
                shutil.copy2(src_skill, str(dst_skill_dir / sfname))
                skills_copied += 1
                break

    # Copy workflows whose domain matches this agent's domain (fuzzy match)
    workflows_copied = 0
    all_wfs = manifest._data.get("workflows", {})
    for wf_name, wf_info in all_wfs.items():
        if not isinstance(wf_info, dict):
            continue
        wf_domain = wf_info.get("domain", "")
        # Match: exact domain, or one contains the other
        if wf_domain == domain or domain in wf_domain or wf_domain in domain:
            wf_path = wf_info.get("path", "")
            if wf_path:
                wf_fname = os.path.basename(wf_path)
                dst_wf_dir = _LOCAL_WORKFLOWS_ROOT / domain
                dst_wf_dir.mkdir(parents=True, exist_ok=True)
                for ref_root in _get_ref_roots():
                    src_wf = os.path.join(ref_root, wf_path)
                    if os.path.isfile(src_wf):
                        shutil.copy2(src_wf, str(dst_wf_dir / wf_fname))
                        workflows_copied += 1
                        break

    _invalidate_domain_cache()   # installed status changed
    return {
        "agent_name": agent_name,
        "domain": domain,
        "agent_installed": installed,
        "skills_copied": skills_copied,
        "skills_total": len(skill_paths or []),
        "workflows_copied": workflows_copied,
    }


def _get_ref_roots() -> List[str]:
    """Get absolute paths to reference project roots."""
    refs = []
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ref_main = os.path.join(base, "参考项目", "automotive-claude-code-agents-main")
    ref_v2 = os.path.join(base, "参考项目", "automotive-claude-code-agents")
    if os.path.isdir(ref_main):
        refs.append(ref_main)
    if os.path.isdir(ref_v2):
        refs.append(ref_v2)
    return refs


@router.get("/list")
async def list_agents():
    """List all available agents from the manifest."""
    manifest = _get_manifest()
    all_agents = manifest.list_agents()
    return {"agents": all_agents, "count": len(all_agents)}


@router.get("/domains")
async def list_domains():
    """List all domains from the manifest."""
    manifest = _get_manifest()
    domains = manifest.list_domains()
    return {"domains": domains}


# ── In-memory cache for expensive domain detail computation ──
import time as _time
_domain_detail_cache = {"data": None, "ts": 0, "ttl": 30}  # seconds


def _invalidate_domain_cache():
    """Force invalidate the domain detail cache (call after download/install)."""
    _domain_detail_cache["data"] = None
    _domain_detail_cache["ts"] = 0


@router.get("/domains-detail")
async def get_domains_detail():
    """
    Return full domain hierarchy: domain → { agents, skills, dependency_edges }.
    Used by the Agent Market to render the 2-level drill-down UI.
    Cached in-memory for 30s to avoid re-parsing 6MB JSON on every tab switch.
    """
    now = _time.time()
    if _domain_detail_cache["data"] is not None and (now - _domain_detail_cache["ts"]) < _domain_detail_cache["ttl"]:
        return _domain_detail_cache["data"]

    manifest = _get_manifest()
    agents = manifest._agents
    skills = manifest._data.get("skill_index", {})

    # Build domain → agents + skills mapping
    domains = {}
    for agent_name, info in agents.items():
        domain = info.get("domain", "unknown")
        if domain not in domains:
            domains[domain] = {"agents": [], "skills": {}, "dependency_edges": [], "workflows": []}
        # Agent entry
        local_path = _local_agent_path(info.get("agent_file", ""))
        installed = local_path is not None and os.path.isfile(local_path)
        agent_entry = {
            "name": agent_name,
            "description": info.get("description", ""),
            "agent_file": info.get("agent_file", ""),
            "author": info.get("author", ""),
            "source_repo": info.get("source_repo", ""),
            "source_url": info.get("source_url", ""),
            "installed": installed,
            "capabilities": info.get("capabilities", []),
            "capability_count": len(info.get("capabilities", [])),
            "skill_count": len(info.get("required_skills", [])),
            "tool_dependencies": info.get("tool_dependencies", []),
            "expertise_areas": info.get("expertise_areas", []),
        }
        domains[domain]["agents"].append(agent_entry)

        # Record agent→skill dependency edges
        for skill in info.get("required_skills", []):
            skill_name = skill.get("name", "") if isinstance(skill, dict) else str(skill)
            skill_path = skill.get("path", "") if isinstance(skill, dict) else ""
            if skill_name:
                domains[domain]["dependency_edges"].append({
                    "source": agent_name,
                    "target": skill_name,
                    "type": "requires",
                })
                # Also ensure the skill is in the domain's skill list
                if skill_name not in domains[domain]["skills"]:
                    sk_installed = _local_skill_path(skill_path) is not None
                    domains[domain]["skills"][skill_name] = {
                        "name": skill_name,
                        "description": "",
                        "path": skill_path,
                        "used_by": [agent_name],
                        "author": "",
                        "source_repo": "",
                        "source_url": "",
                        "installed": sk_installed,
                    }
                else:
                    if agent_name not in domains[domain]["skills"][skill_name].get("used_by", []):
                        domains[domain]["skills"][skill_name].setdefault("used_by", []).append(agent_name)

    # Enrich skills with description from skill_index
    for skill_name, skill_info in skills.items():
        category = skill_info.get("category", "unknown")
        desc = skill_info.get("description", "")
        path = skill_info.get("path", "")
        used_by = skill_info.get("used_by", [])

        for domain_name in list(domains.keys()):
            # Match skill to domain by category
            if category == domain_name or category.startswith(domain_name):
                if skill_name not in domains[domain_name]["skills"]:
                    sk_path = skill_info.get("path", "")
                    sk_installed2 = _local_skill_path(sk_path) is not None
                    domains[domain_name]["skills"][skill_name] = {
                        "name": skill_name,
                        "description": desc if isinstance(desc, str) else "",
                        "path": sk_path,
                        "used_by": used_by,
                        "author": skill_info.get("author", ""),
                        "source_repo": skill_info.get("source_repo", ""),
                        "source_url": skill_info.get("source_url", ""),
                        "installed": sk_installed2,
                    }

    # ── Load standalone workflows from manifest (from /workflows/ directory) ──
    standalone_wfs = manifest._data.get("workflows", {})
    for wf_name, wf_info in standalone_wfs.items():
        if not isinstance(wf_info, dict):
            continue
        wf_domain = wf_info.get("domain", "unknown")
        if wf_domain not in domains:
            domains[wf_domain] = {"agents": [], "skills": {}, "dependency_edges": [], "workflows": []}
        # Check if this workflow file exists locally
        wf_path = wf_info.get("path", "")
        wf_installed = _local_workflow_path(wf_path) is not None
        domains[wf_domain]["workflows"].append({
            "name": wf_name,
            "description": wf_info.get("description", ""),
            "steps": wf_info.get("step_count", 0),
            "agent": "",
            "author": wf_info.get("author", ""),
            "source_repo": wf_info.get("source_repo", ""),
            "path": wf_path,
            "installed": wf_installed,
            "safety_level": wf_info.get("safety_level", ""),
            "trigger": wf_info.get("trigger", ""),
        })

    # Convert skills dict to list
    result_domains = []
    for domain_name, data in sorted(domains.items()):
        agent_count = len(data["agents"])
        skill_list = list(data["skills"].values())
        result_domains.append({
            "name": domain_name,
            "agent_count": agent_count,
            "skill_count": len(skill_list),
            "workflow_count": len(data.get("workflows", [])),
            "agents": sorted(data["agents"], key=lambda a: a["name"]),
            "skills": sorted(skill_list, key=lambda s: s["name"]),
            "workflows": sorted(data.get("workflows", []), key=lambda w: w["name"]),
            "dependency_edges": data["dependency_edges"],
        })

    result = {"domains": result_domains, "count": len(result_domains)}
    _domain_detail_cache["data"] = result
    _domain_detail_cache["ts"] = _time.time()
    return result


@router.get("/{agent_name}")
async def get_agent_info(agent_name: str):
    """Get detailed info for a specific agent."""
    manifest = _get_manifest()
    agent = manifest.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return agent
