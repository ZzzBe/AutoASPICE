"""
Routing analysis router — multi-factor agent routing for automotive tasks.

Endpoints:
  POST /routing/analyze   — score + rank agents for a task
  POST /routing/fan-out   — produce a parallel dispatch plan
  POST /routing/consensus — merge parallel expert outputs into consensus
  POST /routing/suggest   — alias for /analyze (backward-compatible)
"""

from fastapi import APIRouter
from typing import List
import logging
import os

from shared.models import (
    RoutingRequest,
    RoutingRequestEnhanced,
    RoutingResponse,
    AgentSuggestion,
    RouterResult,
    ConsensusRequest,
    ConsensusResult,
)
from shared.state import get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routing", tags=["routing"])


def _get_router():
    """Get the AgentRouter service, with a fallback to basic keyword routing."""
    router_svc = get_service("agent_router")
    if router_svc is None:
        logger.warning("AgentRouter service not available; routing will be limited.")
    return router_svc


# ── Legacy domain patterns (fallback when manifest is unavailable) ─
DOMAIN_PATTERNS = {
    "adas": {
        "keywords": [
            "adas", "perception", "lidar", "radar", "camera", "sensor fusion",
            "planning", "control", "autonomous", "lane", "tracking", "fusion",
            "object detection", "parking", "steering", "acc", "cruise",
            "sensor", "camera calibration", "point cloud",
        ],
        "file_exts": [".c", ".cpp", ".h", ".hpp", ".py"],
        "agents": ["perception-engineer", "control-engineer", "planning-engineer"],
    },
    "functional-safety": {
        "keywords": [
            "iso 26262", "asil", "fmea", "fta", "hara", "safety",
            "hazard", "functional safety", "safety case", "safety goal",
            "fault tree", "failure mode", "risk assessment",
        ],
        "file_exts": [".pdf", ".docx", ".md", ".xlsx"],
        "agents": ["hara-specialist", "fmea-analyst", "safety-case-writer"],
    },
    "sotif": {
        "keywords": [
            "iso 21448", "sotif", "triggering condition", "odd",
            "operational design domain", "functional insufficiency",
            "scenario catalog", "unknown unsafe", "known unsafe",
            "residual risk", "validation strategy",
        ],
        "file_exts": [".pdf", ".md", ".xml", ".xosc"],
        "agents": ["sotif-analyst"],
    },
    "autosar": {
        "keywords": [
            "autosar", "swc", "rte", "bsw", "arxml", "ara-com",
            "ara-diag", "classic platform", "adaptive platform",
            "software component", "runnable",
        ],
        "file_exts": [".arxml", ".xml", ".c", ".h"],
        "agents": ["architect"],
    },
    "diagnostics": {
        "keywords": [
            "uds", "obd", "odx", "pdx", "flash", "bootloader",
            "diagnostics", "dtc", "diagnostic trouble code",
            "iso 14229", "doip", "obd-ii", "can",
        ],
        "file_exts": [".c", ".h", ".odx", ".pdx"],
        "agents": ["diagnostic-engineer"],
    },
    "cybersecurity": {
        "keywords": [
            "iso 21434", "tara", "cybersecurity", "secoc", "crypto",
            "penetration", "secure boot", "ids", "key management",
        ],
        "file_exts": [".c", ".h", ".pem", ".key"],
        "agents": ["automotive-security-architect", "tara-analyst", "penetration-tester"],
    },
    "v2x": {
        "keywords": [
            "v2x", "dsrc", "c-v2x", "platooning", "cooperative",
            "someip", "ethernet", "ieee 802.11p",
        ],
        "file_exts": [".c", ".cpp", ".h"],
        "agents": ["v2x-system-engineer", "v2x-security-specialist"],
    },
    "powertrain": {
        "keywords": [
            "powertrain", "engine", "motor", "transmission", "combustion",
            "ecm", "tcm", "chassis", "esc", "eps", "abs",
        ],
        "file_exts": [".c", ".h", ".mdl", ".slx"],
        "agents": ["powertrain-control-engineer", "chassis-systems-engineer"],
    },
    "cloud": {
        "keywords": [
            "cloud", "aws", "azure", "ota", "fleet", "data lake",
            "digital twin", "iot", "telematics",
        ],
        "file_exts": [".py", ".yaml", ".json", ".tf"],
        "agents": ["aws-iot-automotive-engineer", "fleet-analytics-engineer"],
    },
    "testing": {
        "keywords": [
            "hil", "sil", "mil", "test", "hardware-in-loop",
            "software-in-loop", "simulation", "regression",
        ],
        "file_exts": [".py", ".c", ".yaml"],
        "agents": ["hil-test-engineer", "sil-test-engineer", "test-automation"],
    },
}


def _legacy_score_domain(text: str, file_exts: List[str], domain_config: dict) -> float:
    """Fallback domain scorer (used when manifest is unavailable)."""
    score = 0.0
    text_lower = text.lower()

    kw_matches = sum(1 for kw in domain_config["keywords"] if kw.lower() in text_lower)
    if domain_config["keywords"]:
        score += (kw_matches / max(len(domain_config["keywords"]), 1)) * 0.7

    ext_matches = sum(1 for ext in file_exts if ext in domain_config["file_exts"])
    if file_exts:
        score += (ext_matches / max(len(file_exts), 1)) * 0.3

    return score


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/analyze", response_model=RouterResult)
async def analyze_routing(req: RoutingRequestEnhanced):
    """
    Analyze a task and return ranked agent suggestions with optional fan-out plan.

    Uses the multi-factor AgentRouter when available; falls back to legacy
    keyword matching otherwise.
    """
    router_svc = _get_router()

    # Collect file extensions
    file_exts: List[str] = []
    for fname in req.uploaded_files:
        _, ext = os.path.splitext(fname)
        if ext:
            file_exts.append(ext.lower())

    if router_svc is not None:
        # ── Use the full AgentRouter engine ──
        result = await router_svc.route(
            text_instruction=req.text_instruction,
            uploaded_files=req.uploaded_files,
            file_contents=req.file_contents,
            user_preferences=req.user_preferences,
            require_consensus=req.require_consensus,
            max_parallel_agents=req.max_parallel_agents,
            llm_config=req.llm_config,
        )
        return result

    # ── Fallback: legacy keyword routing ──
    combined_text = req.text_instruction
    for content in (req.file_contents or {}).values():
        combined_text += " " + content[:2000]

    domain_scores = []
    for domain, config in DOMAIN_PATTERNS.items():
        score = _legacy_score_domain(combined_text, file_exts, config)
        if score > 0:
            domain_scores.append((domain, score, config))

    domain_scores.sort(key=lambda x: -x[1])

    suggestions = []
    seen_agents = set()
    for domain, score, config in domain_scores:
        for agent_name in config["agents"]:
            if agent_name not in seen_agents and len(suggestions) < 5:
                seen_agents.add(agent_name)
                matched_kws = [kw for kw in config["keywords"]
                               if kw.lower() in combined_text.lower()]
                reason = f"Matched domain '{domain}'"
                if matched_kws:
                    reason += f" via keywords: {', '.join(matched_kws[:5])}"
                if file_exts:
                    matched_exts = [e for e in file_exts if e in config["file_exts"]]
                    if matched_exts:
                        reason += f" and file types: {', '.join(matched_exts)}"

                suggestions.append(AgentSuggestion(
                    agent_name=agent_name,
                    domain=domain,
                    confidence=round(min(score, 0.99), 2),
                    reason=reason,
                    required_skills=[],
                ))

    detected = [d for d, _, _ in domain_scores[:3]]

    if not suggestions:
        suggestions = [
            AgentSuggestion(
                agent_name="perception-engineer",
                domain="adas",
                confidence=0.3,
                reason="No strong domain match found. ADAS is the most common starting point.",
                required_skills=[],
            ),
            AgentSuggestion(
                agent_name="hara-specialist",
                domain="functional-safety",
                confidence=0.2,
                reason="Safety analysis is recommended for all automotive projects.",
                required_skills=[],
            ),
        ]

    return RouterResult(
        suggestions=suggestions,
        fan_out_plan=[],
        detected_domains=detected,
        parsed_metadata={"mode": "legacy_fallback"},
    )


@router.post("/suggest", response_model=RouterResult)
async def suggest_agents(req: RoutingRequestEnhanced):
    """Alias for /analyze (backward-compatible)."""
    return await analyze_routing(req)


@router.post("/fan-out", response_model=RouterResult)
async def fan_out_routing(req: RoutingRequestEnhanced):
    """
    Produce a fan-out dispatch plan — best agent per detected domain.

    This endpoint forces fan-out mode regardless of task complexity.
    """
    router_svc = _get_router()

    combined_text = req.text_instruction
    for content in (req.file_contents or {}).values():
        combined_text += " " + content[:2000]

    if router_svc is not None:
        from shared.models import FanOutSubTask

        metadata = router_svc.parse_task(combined_text)
        prefs = req.user_preferences or {}

        # Score all agents
        scored = []
        for agent_name in router_svc._list_all_agent_names():
            score, _ = router_svc.score_agent(agent_name, combined_text, metadata, prefs)
            if score > 0.01:
                scored.append((agent_name, score))
        scored.sort(key=lambda x: -x[1])

        fan_out_plan = router_svc._build_fan_out_plan(
            scored, metadata, req.max_parallel_agents,
        )

        # Also produce suggestions from top scored
        suggestions = []
        for agent_name, score in scored[:10]:
            agent = router_svc.manifest.get_agent(agent_name) or {}
            domain = agent.get("domain", "unknown")
            skills = agent.get("required_skills", [])
            skill_names = []
            for sk in skills:
                if isinstance(sk, dict):
                    skill_names.append(sk.get("name", ""))
                elif isinstance(sk, str):
                    skill_names.append(sk)

            suggestions.append(AgentSuggestion(
                agent_name=agent_name,
                domain=domain,
                confidence=round(min(score, 0.99), 2),
                reason=f"Domain: {domain} | score: {score:.3f}",
                required_skills=skill_names[:8],
            ))

        return RouterResult(
            suggestions=suggestions,
            fan_out_plan=fan_out_plan,
            detected_domains=metadata.get("detected_domains", []),
            parsed_metadata=metadata,
        )

    # Fallback
    return await analyze_routing(req)


@router.post("/consensus", response_model=ConsensusResult)
async def build_consensus(req: ConsensusRequest):
    """
    Build consensus from parallel expert agent outputs.

    Accepts a list of agent outputs (each with agent_name, domain, findings)
    and returns agreed findings, disagreements, unique insights, and
    a confidence score.
    """
    router_svc = _get_router()

    if router_svc is not None:
        return router_svc.build_consensus(
            agent_outputs=req.agent_outputs,
            task_description=req.task_description,
            min_agreement_threshold=req.min_agreement_threshold,
        )

    # Fallback: simple majority vote
    agent_outputs = req.agent_outputs
    if len(agent_outputs) < 2:
        return ConsensusResult(
            agreed_findings=[],
            disagreements=[],
            unique_insights=[],
            confidence_score=0.0,
            requires_human_review=True,
            participant_agents=[a.get("agent_name", "") for a in agent_outputs],
        )

    # Collect all claims
    claim_map: dict = {}
    for output in agent_outputs:
        agent_name = output.get("agent_name", "unknown")
        for f in output.get("findings", []):
            claim = f.get("claim", "")
            if claim not in claim_map:
                claim_map[claim] = []
            claim_map[claim].append({
                "agent": agent_name,
                "confidence": f.get("confidence", 0),
            })

    agreed = []
    unique = []
    for claim, sources in claim_map.items():
        if len(sources) >= req.min_agreement_threshold:
            agreed.append({
                "claim": claim,
                "confidence": max(s.get("confidence", 0) for s in sources),
                "supporting_agents": [s["agent"] for s in sources],
            })
        else:
            unique.append({
                "claim": claim,
                "confidence": sources[0].get("confidence", 0) if sources else 0,
                "source_agent": sources[0]["agent"] if sources else "",
            })

    return ConsensusResult(
        agreed_findings=agreed,
        disagreements=[],
        unique_insights=unique,
        confidence_score=round(len(agreed) / max(len(claim_map), 1), 3),
        requires_human_review=len(agreed) < len(claim_map),
        participant_agents=[a.get("agent_name", "") for a in agent_outputs],
    )
