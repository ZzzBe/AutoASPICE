"""
AgentRouter — Skill-level weighted routing engine.

Routes automotive-engineering tasks to the best-matching Domain Expert Agents
using a five-factor weighted scoring model:

    Score = 0.30 * Expertise_Match
          + 0.25 * Tool_Availability
          + 0.20 * Keyword_Match
          + 0.15 * Preference
          + 0.10 * License_Status

Also provides Fan-Out / Fan-In dispatch planning and a consensus builder
for merging parallel expert outputs.
"""

import re
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Set

from agent_engine.manifest import ManifestReader

logger = logging.getLogger(__name__)

# ── Scoring weights ──────────────────────────────────────────────
W_EXPERTISE = 0.30
W_TOOLS = 0.25
W_KEYWORDS = 0.20
W_PREFERENCE = 0.15
W_LICENSE = 0.10

# ── Known automotive standards for metadata extraction ───────────
KNOWN_STANDARDS = [
    "ISO 26262", "ISO 21448", "ISO 21434", "ISO 14229", "ISO 15765",
    "ASPICE", "AUTOSAR", "MISRA", "UN R155", "UN R156", "SAE J3016",
    "SAE J3061", "IEC 61508", "ISO 16750", "ISO 11898",
]

KNOWN_TOOLS_PATTERNS = [
    "Vector DaVinci", "EB tresos", "Medini Analyze", "CANoe", "CANalyzer",
    "INCA", "MDA", "CARLA", "MATLAB", "Simulink", "TRACE32", "Lauterbach",
    "Polarion", "DOORS", "Jenkins", "GitLab CI", "QNX", "Elektrobit",
    "AUTOSAR Builder", "SystemWeaver", "codebeamer", "PTC Integrity",
    "ANSYS", "dSPACE", "ETAS", "VectorCAST", "Tessy", "Polyspace",
    "GrammaTech", "Coverity", "Klocwork", "SonarQube",
]

# ── Lifecycle phase keywords ─────────────────────────────────────
LIFECYCLE_PHASES = {
    "concept": ["concept", "item definition", "early phase", "preliminary"],
    "development": ["development", "implementation", "coding", "design", "architecture"],
    "validation": ["validation", "verification", "testing", "hil", "sil", "mil"],
    "production": ["production", "manufacturing", "release", "deployment", "sop"],
    "operation": ["operation", "maintenance", "field", "fleet", "monitoring"],
}


class AgentRouter:
    """
    Multi-factor agent router for automotive engineering tasks.

    Uses the full agent manifest (capabilities, expertise, tool dependencies,
    domain associations) to compute weighted relevance scores and produce
    ranked routing suggestions, fan-out dispatch plans, and consensus results.
    """

    def __init__(self, manifest: ManifestReader):
        self.manifest = manifest
        # Cache agent summaries for fast scoring (built lazily)
        self._agent_cache: Dict[str, Dict[str, Any]] = {}

    # ── Public API ────────────────────────────────────────────────

    async def route(
        self,
        text_instruction: str,
        uploaded_files: Optional[List[str]] = None,
        file_contents: Optional[Dict[str, str]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        require_consensus: bool = False,
        max_parallel_agents: int = 5,
        llm_config: Any = None,
    ) -> "RouterResult":  # noqa: F821
        """
        Main routing entry point.

        1. Parse the task to extract metadata.
        2. Score every candidate agent in the manifest (Step 1a: coarse).
        3. If llm_config is available, re-rank top candidates via LLM (Step 1b: fine).
        4. Rank and return top suggestions.
        5. If the task spans multiple domains or require_consensus is True,
           produce a fan-out dispatch plan.
        """
        from shared.models import RouterResult, AgentSuggestion, FanOutSubTask

        uploaded_files = uploaded_files or []
        file_contents = file_contents or {}
        user_preferences = user_preferences or {}

        # Step 1 — combine text sources
        combined_text = text_instruction
        for content in file_contents.values():
            combined_text += " " + content[:2000]

        # Extract file extensions
        import os
        file_exts = set()
        for fname in uploaded_files:
            _, ext = os.path.splitext(fname)
            if ext:
                file_exts.add(ext.lower())

        # Step 2 — parse metadata
        metadata = self.parse_task(combined_text, list(file_exts))

        # Step 3 — compute the set of domains that should be scored.
        # Generic domains are only included when no specific domain was detected
        # or when the task explicitly mentions project-management keywords.
        detected = metadata.get("detected_domains", [])
        adjacent_map: Dict[str, List[str]] = {
            "adas": ["functional-safety", "sotif", "autosar", "testing", "calibration"],
            "functional-safety": ["adas", "sotif", "autosar", "cybersecurity", "testing"],
            "sotif": ["adas", "functional-safety", "testing"],
            "autosar": ["functional-safety", "diagnostics", "cybersecurity", "adas"],
            "diagnostics": ["autosar", "functional-safety", "cybersecurity"],
            "cybersecurity": ["functional-safety", "autosar", "diagnostics", "v2x"],
            "v2x": ["adas", "cybersecurity", "cloud"],
            "powertrain": ["adas", "testing", "calibration"],
            "cloud": ["v2x", "cybersecurity", "testing"],
            "testing": ["adas", "functional-safety", "autosar", "powertrain"],
            "calibration": ["adas", "powertrain", "testing"],
        }
        allowed_domains: Set[str] = set(detected)
        for d in detected:
            for adj in adjacent_map.get(d, []):
                allowed_domains.add(adj)
        # Always allow a few core/utility domains at low priority
        allowed_domains |= {"automotive-workflow", "orchestration"}

        has_specific_domains = bool(
            detected and any(d not in self._GENERIC_DOMAINS for d in detected)
        )

        # Step 4 — score agents, filtering to relevant domains when possible
        scored = []
        for agent_name in self._list_all_agent_names():
            agent = self.manifest.get_agent(agent_name) or {}
            agent_domain = agent.get("domain", "")

            # Domain gate: when specific domains are detected, skip agents
            # outside the relevant-domain set to keep results focused.
            if has_specific_domains and agent_domain not in allowed_domains:
                continue

            score, breakdown = self.score_agent(
                agent_name=agent_name,
                task_text=combined_text,
                parsed_metadata=metadata,
                preferences=user_preferences,
            )
            if score > 0.001:
                scored.append((agent_name, score, breakdown))

        # If filtering left us with too few candidates, relax and rescore all
        if len(scored) < 5:
            logger.info("Domain filter returned < 5 agents; falling back to full manifest.")
            scored.clear()
            for agent_name in self._list_all_agent_names():
                score, breakdown = self.score_agent(
                    agent_name=agent_name,
                    task_text=combined_text,
                    parsed_metadata=metadata,
                    preferences=user_preferences,
                )
                if score > 0.001:
                    scored.append((agent_name, score, breakdown))

        # Sort descending by score
        scored.sort(key=lambda x: -x[1])

        # Step 3b — LLM fine-ranking (Step 1b) if config is available
        llm_rerank_info = None
        if llm_config and self._has_llm_config(llm_config) and len(scored) >= 3:
            try:
                scored, llm_rerank_info = await self._llm_rerank(
                    scored=scored,
                    task_text=combined_text,
                    metadata=metadata,
                    llm_config=llm_config,
                )
            except Exception as e:
                logger.warning(f"LLM re-rank failed, using coarse scores: {e}")

        # Step 4 — build suggestions (top 10)
        suggestions = []
        seen_domains = set()
        for agent_name, score, breakdown in scored[:10]:
            agent = self.manifest.get_agent(agent_name) or {}
            domain = agent.get("domain", "unknown")
            seen_domains.add(domain)

            # Build a human-readable reason
            reason_parts = []
            if breakdown["expertise"] > 0.15:
                reason_parts.append(f"expertise match ({breakdown['expertise']:.2f})")
            if breakdown["tools"] > 0.10:
                reason_parts.append(f"tool availability ({breakdown['tools']:.2f})")
            if breakdown["keywords"] > 0.05:
                reason_parts.append(f"keyword match ({breakdown['keywords']:.2f})")

            reason = f"Domain: {domain}"
            if reason_parts:
                reason += " | " + ", ".join(reason_parts)

            # Extract skill names
            skills = agent.get("required_skills", [])
            skill_names: List[str] = []
            for sk in skills:
                if isinstance(sk, dict):
                    skill_names.append(sk.get("name", ""))
                elif isinstance(sk, str):
                    skill_names.append(sk)

            suggestions.append(AgentSuggestion(
                agent_name=agent_name,
                domain=domain,
                confidence=round(min(score, 0.99), 2),
                reason=reason,
                required_skills=skill_names[:8],
            ))

        # Step 5 — fan-out plan for multi-domain / consensus-required tasks
        fan_out_plan: list = []
        is_complex = (
            require_consensus
            or len(detected) >= 2
            or metadata.get("is_complex_task", False)
        )
        if is_complex and len(scored) >= 2:
            fan_out_plan = self._build_fan_out_plan(
                scored=scored,
                metadata=metadata,
                max_agents=max_parallel_agents,
            )

        return RouterResult(
            suggestions=suggestions,
            fan_out_plan=fan_out_plan,
            detected_domains=detected,  # use parsed domains, not agent domains
            parsed_metadata=metadata,
        )

    def score_agent(
        self,
        agent_name: str,
        task_text: str,
        parsed_metadata: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute the weighted relevance score for a single agent against a task.

        Returns (total_score, breakdown_dict).
        """
        agent = self.manifest.get_agent(agent_name)
        if agent is None:
            return 0.0, {"expertise": 0.0, "tools": 0.0, "keywords": 0.0,
                         "preference": 0.0, "license": 0.0, "total": 0.0}

        metadata = parsed_metadata or {}
        prefs = preferences or {}

        expertise = self._score_expertise(task_text, agent, metadata)
        tools = self._score_tools(task_text, agent, metadata)
        keywords = self._score_keywords(task_text, agent, metadata)
        preference = self._score_preference(agent_name, agent, prefs)
        license_score = self._score_license(agent, prefs)

        total = (
            W_EXPERTISE * expertise
            + W_TOOLS * tools
            + W_KEYWORDS * keywords
            + W_PREFERENCE * preference
            + W_LICENSE * license_score
        )

        return total, {
            "expertise": round(expertise, 3),
            "tools": round(tools, 3),
            "keywords": round(keywords, 3),
            "preference": round(preference, 3),
            "license": round(license_score, 3),
            "total": round(total, 3),
        }

    def parse_task(
        self,
        task_text: str,
        file_exts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured metadata from a natural-language task description.

        Returns a dict with keys like:
          - detected_domains
          - detected_standards
          - detected_tools
          - safety_level (QM / ASIL A/B/C/D)
          - lifecycle_phase
          - is_complex_task
          - extracted_keywords
          - file_exts
        """
        text_lower = task_text.lower()

        # Standards detection
        standards = [s for s in KNOWN_STANDARDS if s.lower() in text_lower]

        # Tool detection
        tools = [t for t in KNOWN_TOOLS_PATTERNS if t.lower() in text_lower]

        # ASIL / safety level detection (handles "ASIL D", "ASIL-D", "ASILD")
        safety_level = "QM"
        if re.search(r"ASIL[\s\-]*D", task_text, re.IGNORECASE):
            safety_level = "ASIL D"
        elif re.search(r"ASIL[\s\-]*C", task_text, re.IGNORECASE):
            safety_level = "ASIL C"
        elif re.search(r"ASIL[\s\-]*B", task_text, re.IGNORECASE):
            safety_level = "ASIL B"
        elif re.search(r"ASIL[\s\-]*A", task_text, re.IGNORECASE):
            safety_level = "ASIL A"

        # Lifecycle phase
        lifecycle = "development"  # default
        for phase, kw_list in LIFECYCLE_PHASES.items():
            if any(kw in text_lower for kw in kw_list):
                lifecycle = phase
                break

        # Domain detection from keyword patterns
        detected_domains = self._detect_domains(text_lower)

        # Extract meaningful keywords (nouns, technical terms)
        extracted_keywords = self._extract_keywords(text_lower)

        # Complexity heuristic: multi-domain, high ASIL, or explicit consensus ask
        is_complex = (
            len(detected_domains) >= 2
            or safety_level in ("ASIL C", "ASIL D")
            or "consensus" in text_lower
            or "multi-agent" in text_lower
        )

        return {
            "detected_domains": detected_domains,
            "detected_standards": standards,
            "detected_tools": tools,
            "safety_level": safety_level,
            "lifecycle_phase": lifecycle,
            "is_complex_task": is_complex,
            "extracted_keywords": extracted_keywords,
            "file_exts": file_exts or [],
        }

    def fan_out(
        self,
        task_text: str,
        max_agents: int = 5,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> List["FanOutSubTask"]:  # noqa: F821
        """
        Produce a fan-out dispatch plan by identifying independent sub-tasks
        and assigning each to the best-matching agent.
        """
        from shared.models import FanOutSubTask

        metadata = self.parse_task(task_text)
        prefs = user_preferences or {}

        # Score all agents
        scored = []
        for agent_name in self._list_all_agent_names():
            score, _breakdown = self.score_agent(agent_name, task_text, metadata, prefs)
            if score > 0.01:
                scored.append((agent_name, score))
        scored.sort(key=lambda x: -x[1])

        return self._build_fan_out_plan(scored, metadata, max_agents)

    def build_consensus(
        self,
        agent_outputs: List[Dict[str, Any]],
        task_description: str = "",
        min_agreement_threshold: int = 2,
    ) -> "ConsensusResult":  # noqa: F821
        """
        Merge parallel expert outputs into a consensus view.

        Each entry in agent_outputs should have:
          - agent_name (str)
          - domain (str)
          - findings (list of dicts, each with at least 'claim' and 'confidence')

        The consensus builder:
          1. Clusters findings by semantic overlap (key-phrase Jaccard)
          2. Marks findings agreed by >= min_agreement_threshold agents
          3. Identifies unique insights (only one agent)
          4. Flags disagreements (conflicting claims on same topic)
          5. Computes aggregate confidence
        """
        from shared.models import ConsensusResult

        if len(agent_outputs) < 2:
            return ConsensusResult(
                agreed_findings=[],
                disagreements=[],
                unique_insights=[],
                confidence_score=0.0,
                requires_human_review=True,
                participant_agents=[a.get("agent_name", "") for a in agent_outputs],
            )

        # Collect all findings with source agent info
        all_findings: List[Dict[str, Any]] = []
        for output in agent_outputs:
            agent_name = output.get("agent_name", "unknown")
            domain = output.get("domain", "")
            findings = output.get("findings", [])
            for f in findings:
                all_findings.append({
                    **f,
                    "_agent": agent_name,
                    "_domain": domain,
                })

        if not all_findings:
            return ConsensusResult(
                agreed_findings=[],
                disagreements=[],
                unique_insights=[],
                confidence_score=0.0,
                requires_human_review=True,
                participant_agents=[a.get("agent_name", "") for a in agent_outputs],
            )

        # Cluster findings by claim similarity
        clusters = self._cluster_findings(all_findings)

        agreed: List[Dict[str, Any]] = []
        disagreements: List[Dict[str, Any]] = []
        unique_insights: List[Dict[str, Any]] = []

        for cluster in clusters:
            agents_involved = list(set(f["_agent"] for f in cluster))
            if len(agents_involved) >= min_agreement_threshold:
                # Majority agreement — take the highest-confidence version
                best = max(cluster, key=lambda f: f.get("confidence", 0))
                agreed.append({
                    "claim": best.get("claim", ""),
                    "confidence": best.get("confidence", 0),
                    "supporting_agents": agents_involved,
                    "source": best.get("_domain", ""),
                })
            elif len(agents_involved) == 1:
                # Single-agent insight
                f = cluster[0]
                unique_insights.append({
                    "claim": f.get("claim", ""),
                    "confidence": f.get("confidence", 0),
                    "source_agent": f["_agent"],
                    "source_domain": f.get("_domain", ""),
                })
            else:
                # Disagreement — conflicting or divergent views
                disagreements.append({
                    "topic": cluster[0].get("claim", "")[:120],
                    "perspectives": [
                        {"agent": f["_agent"], "claim": f.get("claim", ""),
                         "confidence": f.get("confidence", 0)}
                        for f in cluster
                    ],
                })

        # Aggregate confidence: average of agreed findings, discounted by
        # the proportion of findings that reached agreement.
        if all_findings:
            agreement_rate = len([f for c in clusters
                                  if len(set(x["_agent"] for x in c)) >= min_agreement_threshold
                                  for f in c]) / len(all_findings)
        else:
            agreement_rate = 0.0

        avg_confidence = (
            sum(a.get("confidence", 0) for a in agreed) / max(len(agreed), 1)
            if agreed else 0.0
        )
        aggregate_confidence = round(avg_confidence * (0.5 + 0.5 * agreement_rate), 3)

        needs_review = len(disagreements) > 0 or agreement_rate < 0.5

        return ConsensusResult(
            agreed_findings=agreed,
            disagreements=disagreements,
            unique_insights=unique_insights,
            confidence_score=aggregate_confidence,
            requires_human_review=needs_review,
            participant_agents=[a.get("agent_name", "") for a in agent_outputs],
        )

    # ── Scoring sub-methods ───────────────────────────────────────

    # Domains that should only rank high when explicitly relevant
    _GENERIC_DOMAINS = {
        "project-management", "core", "general", "unknown",
    }

    # Stopwords filtered from token comparison to avoid inflating overlap
    _STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "and", "or", "not",
        "no", "but", "if", "then", "else", "when", "where", "which", "who",
        "whom", "this", "that", "these", "those", "it", "its", "we", "you",
        "they", "he", "she", "i", "my", "your", "our", "their", "me", "him",
        "her", "us", "them", "also", "each", "all", "any", "both", "such",
    }

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """Tokenize text, filtering stopwords and short tokens."""
        tokens = set()
        for token in text.lower().split():
            # Strip punctuation from token edges
            token = token.strip(".,;:()[]{}!?\"'")
            if token and token not in AgentRouter._STOPWORDS and len(token) >= 2:
                tokens.add(token)
        return tokens

    def _score_expertise(
        self, task_text: str, agent: Dict[str, Any], metadata: Dict[str, Any]
    ) -> float:
        """
        Score how well the agent's expertise matches the task.
        Compares task text against:
          - expertise_areas (primary — each match = 1 point)
          - capabilities (secondary — each match = 0.5 points)

        Applies a domain-relevance multiplier:
          - 1.5x if agent's domain is in detected_domains
          - 0.4x if agent's domain is a generic catch-all domain
        """
        task_lower = task_text.lower()
        task_tokens = self._tokenize(task_lower)
        if not task_tokens:
            return 0.0

        expertise_areas = agent.get("expertise_areas", [])
        capabilities = agent.get("capabilities", [])

        if not expertise_areas and not capabilities:
            # Fall back to description matching
            desc = agent.get("description", "").lower()
            desc_tokens = self._tokenize(desc)
            if not desc_tokens:
                return 0.0
            token_overlap = task_tokens & desc_tokens
            return min(len(token_overlap) / max(len(desc_tokens), 1), 1.0)

        total_possible = len(expertise_areas) + 0.5 * len(capabilities)
        if total_possible == 0:
            return 0.0

        matched = 0.0

        for area in expertise_areas:
            area_lower = area.lower()
            if area_lower in task_lower:
                matched += 1.0
            else:
                area_tokens = self._tokenize(area_lower)
                if not area_tokens:
                    continue
                token_overlap = task_tokens & area_tokens
                threshold = max(1, len(area_tokens) * 0.2)
                if len(token_overlap) >= threshold:
                    matched += 0.7
                elif len(token_overlap) >= 1 and len(token_overlap) / len(task_tokens) >= 0.05:
                    matched += 0.3

        for cap in capabilities:
            cap_lower = cap.lower()
            if cap_lower in task_lower:
                matched += 0.5
            else:
                cap_tokens = self._tokenize(cap_lower)
                if not cap_tokens:
                    continue
                token_overlap = task_tokens & cap_tokens
                threshold = max(1, len(cap_tokens) * 0.15)
                if len(token_overlap) >= threshold:
                    matched += 0.35
                elif len(token_overlap) >= 1 and len(token_overlap) / len(task_tokens) >= 0.03:
                    matched += 0.15

        raw_score = min(matched / max(total_possible, 1), 1.0)

        # Domain relevance multiplier
        agent_domain = agent.get("domain", "")
        detected_domains = metadata.get("detected_domains", [])

        if agent_domain in detected_domains:
            raw_score *= 1.5  # boost for domain-matched agents
        elif agent_domain in self._GENERIC_DOMAINS:
            raw_score *= 0.4  # penalty for generic catch-all agents

        return round(min(raw_score, 1.0), 4)

    def _score_tools(
        self, task_text: str, agent: Dict[str, Any], metadata: Dict[str, Any]
    ) -> float:
        """
        Score tool availability match.
          - Tools mentioned in the task that the agent requires → high score
          - Agent tools that overlap with system availability → bonus
          - No tool dependencies → low-neutral (0.2 — less penalty than no match)
          - Tool dependencies with no matches → 0.0
        """
        tool_deps = agent.get("tool_dependencies", [])
        if not tool_deps:
            return 0.2  # low-neutral: agent may work without specific tools

        task_lower = task_text.lower()
        detected_tools = set(t.lower() for t in metadata.get("detected_tools", []))

        matches = 0.0
        for tool in tool_deps:
            tool_lower = tool.lower()
            # Check if the tool is mentioned in the task
            if tool_lower in task_lower:
                matches += 1.0
                continue
            # Check if a detected tool name appears in the agent's tool dep
            for dt in detected_tools:
                if dt in tool_lower or tool_lower in dt:
                    matches += 0.8
                    break
            else:
                # Partial keyword match (e.g., "Vector" matches "Vector DaVinci")
                tool_keywords = set(tool_lower.split())
                for dt in detected_tools:
                    dt_keywords = set(dt.split())
                    if len(tool_keywords & dt_keywords) >= 1:
                        matches += 0.5
                        break

        return round(min(matches / max(len(tool_deps), 1), 1.0), 4)

    def _score_keywords(
        self, task_text: str, agent: Dict[str, Any], metadata: Dict[str, Any]
    ) -> float:
        """
        Keyword-match score combining:
          - Domain keyword patterns (legacy DOMAIN_PATTERNS)
          - Agent description overlap
          - Extracted technical keywords vs agent capabilities
        """
        task_lower = task_text.lower()
        task_tokens = set(task_lower.split())

        score = 0.0
        components = 0

        # 1. Description match (0-1)
        desc = agent.get("description", "").lower()
        if desc:
            desc_tokens = set(desc.split())
            if desc_tokens:
                token_overlap = task_tokens & desc_tokens
                score += len(token_overlap) / max(len(desc_tokens), 1)
                components += 1

        # 2. Capability keyword overlap (0-1)
        capabilities = agent.get("capabilities", [])
        if capabilities:
            cap_text = " ".join(capabilities).lower()
            cap_tokens = set(cap_text.split())
            if cap_tokens:
                token_overlap = task_tokens & cap_tokens
                score += len(token_overlap) / max(len(cap_tokens), 1)
                components += 1

        # 3. Extracted keyword match against agent name + domain
        agent_domain = agent.get("domain", "").lower()
        agent_name_lower = agent.get("name", "").lower()
        extracted_kws = set(metadata.get("extracted_keywords", []))
        if extracted_kws:
            domain_hits = sum(
                1 for kw in extracted_kws
                if kw in agent_domain or kw in agent_name_lower
            )
            score += domain_hits / max(len(extracted_kws), 1)
            components += 1

        return round(score / max(components, 1), 4)

    def _score_preference(
        self,
        agent_name: str,
        agent: Dict[str, Any],
        preferences: Dict[str, Any],
    ) -> float:
        """
        Preference boost from:
          - previously_used_agents list (0.5 boost if agent was used before)
          - favorite_agents list (0.7 boost)
          - domain_preference — boost agents in a preferred domain (0.3)
        Capped at 1.0.
        """
        score = 0.0

        prev_used = preferences.get("previously_used_agents", [])
        if agent_name in prev_used:
            score += 0.5

        favorites = preferences.get("favorite_agents", [])
        if agent_name in favorites:
            score += 0.7

        preferred_domains = preferences.get("preferred_domains", [])
        agent_domain = agent.get("domain", "")
        if agent_domain in preferred_domains:
            score += 0.3

        return min(score, 1.0)

    def _score_license(
        self, agent: Dict[str, Any], preferences: Dict[str, Any]
    ) -> float:
        """
        License status score.
        Currently defaults to 1.0 (all licensed) until a license management
        system is integrated. When available, it will check:
          - Are all required tools licensed?
          - Are the agent's skill bundles unlocked?
        """
        # Check if a license map is provided in preferences
        license_map = preferences.get("license_map", {})
        if not license_map:
            return 1.0  # default: assume all licensed

        tool_deps = agent.get("tool_dependencies", [])
        if not tool_deps:
            return 1.0

        licensed_count = 0
        for tool in tool_deps:
            tool_key = tool.lower().replace(" ", "_")
            if license_map.get(tool_key, True):
                licensed_count += 1

        ratio = licensed_count / max(len(tool_deps), 1)
        if ratio >= 1.0:
            return 1.0
        elif ratio >= 0.5:
            return 0.5
        else:
            return 0.0

    # ── Task parsing helpers ──────────────────────────────────────

    def _detect_domains(self, text_lower: str) -> List[str]:
        """Detect which automotive domains are referenced in the task text."""
        # Domain → trigger keywords
        domain_map = {
            "adas": ["adas", "perception", "lidar", "radar", "camera", "sensor fusion",
                     "planning", "control", "autonomous", "lane", "tracking",
                     "object detection", "parking", "steering", "acc", "cruise",
                     "point cloud", "slam", "localization"],
            "functional-safety": ["iso 26262", "asil", "fmea", "fta", "hara", "safety",
                                  "hazard", "functional safety", "safety case", "safety goal",
                                  "fault tree", "failure mode", "risk assessment"],
            "sotif": ["iso 21448", "sotif", "triggering condition", "odd",
                      "operational design domain", "functional insufficiency",
                      "scenario catalog", "unknown unsafe", "known unsafe"],
            "autosar": ["autosar", "swc", "rte", "bsw", "arxml", "ara-com",
                        "ara-diag", "classic platform", "adaptive platform",
                        "software component", "runnable"],
            "diagnostics": ["uds", "obd", "odx", "pdx", "flash", "bootloader",
                            "diagnostics", "dtc", "diagnostic trouble code",
                            "iso 14229", "doip", "obd-ii"],
            "cybersecurity": ["iso 21434", "tara", "cybersecurity", "secoc", "crypto",
                              "penetration", "secure boot", "ids", "key management",
                              "threat modeling", "vulnerability"],
            "v2x": ["v2x", "dsrc", "c-v2x", "platooning", "cooperative",
                    "someip", "ethernet", "ieee 802.11p"],
            "powertrain": ["powertrain", "engine", "motor", "transmission", "combustion",
                           "ecm", "tcm", "chassis", "esc", "eps", "abs"],
            "cloud": ["cloud", "aws", "azure", "ota", "fleet", "data lake",
                      "digital twin", "iot", "telematics"],
            "testing": ["hil", "sil", "mil", "test", "hardware-in-loop",
                        "software-in-loop", "simulation", "regression"],
            "calibration": ["calibration", "xcp", "ccp", "ecu calibration",
                            "parameter tuning", "map optimization"],
        }

        detected = []
        for domain, keywords in domain_map.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(domain)
        return detected

    def _extract_keywords(self, text_lower: str) -> List[str]:
        """Extract meaningful technical keywords from task text."""
        # Remove common stopwords
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "and", "or", "not", "no",
            "but", "if", "then", "else", "when", "where", "which",
            "who", "whom", "this", "that", "these", "those", "it",
            "its", "we", "you", "they", "he", "she", "i", "my", "your",
            "our", "their", "me", "him", "her", "us", "them",
        }

        # Tokenize and filter
        tokens = re.findall(r"[a-z0-9][a-z0-9\-\+\.]*[a-z0-9]|[a-z0-9]", text_lower)
        meaningful = [t for t in tokens if t not in stopwords and len(t) >= 2]

        # Keep unique, preserve order of first occurrence
        seen = set()
        result = []
        for t in meaningful:
            if t not in seen:
                seen.add(t)
                result.append(t)

        return result[:50]  # cap at 50 keywords

    # ── Fan-out / Consensus helpers ───────────────────────────────

    def _build_fan_out_plan(
        self,
        scored: List[Tuple[str, float]],
        metadata: Dict[str, Any],
        max_agents: int,
    ) -> list:
        """Build a fan-out dispatch plan from scored agents and task metadata."""
        from shared.models import FanOutSubTask

        detected_domains = metadata.get("detected_domains", [])
        if not detected_domains:
            detected_domains = ["general"]

        plan = []
        # Assign the best agent per detected domain
        assigned_domains: Set[str] = set()
        for domain in detected_domains:
            if len(plan) >= max_agents:
                break
            # Find the top-scoring agent for this domain
            for agent_name, score, _ in scored:
                agent = self.manifest.get_agent(agent_name)
                if agent is None:
                    continue
                agent_domain = agent.get("domain", "")
                if agent_domain == domain and domain not in assigned_domains:
                    sub_id = f"sub_{domain.replace('-', '_')}_{uuid.uuid4().hex[:6]}"
                    plan.append(FanOutSubTask(
                        sub_task_id=sub_id,
                        description=f"Analyze {domain.replace('-', ' ')} aspects of the task",
                        agent_name=agent_name,
                        domain=domain,
                        confidence=round(min(score, 0.99), 2),
                        required_tools=agent.get("tool_dependencies", [])[:5],
                        input_context={"domain": domain, "metadata": metadata},
                    ))
                    assigned_domains.add(domain)
                    break

        # If we have remaining capacity, add next-best agents from other domains
        if len(plan) < max_agents:
            for agent_name, score, _ in scored:
                if len(plan) >= max_agents:
                    break
                agent = self.manifest.get_agent(agent_name)
                if agent is None:
                    continue
                agent_domain = agent.get("domain", "")
                if agent_domain not in assigned_domains:
                    sub_id = f"sub_{agent_domain.replace('-', '_')}_{uuid.uuid4().hex[:6]}"
                    plan.append(FanOutSubTask(
                        sub_task_id=sub_id,
                        description=f"Cross-domain analysis from {agent_domain.replace('-', ' ')} perspective",
                        agent_name=agent_name,
                        domain=agent_domain,
                        confidence=round(min(score, 0.99), 2),
                        required_tools=agent.get("tool_dependencies", [])[:5],
                        input_context={"domain": agent_domain, "metadata": metadata},
                    ))
                    assigned_domains.add(agent_domain)

        return plan

    def _cluster_findings(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[List[Dict[str, Any]]]:
        """
        Cluster findings by semantic overlap using key-phrase Jaccard similarity.
        Two findings are grouped if their key-phrase overlap exceeds 0.3.
        """
        if len(findings) <= 1:
            return [findings] if findings else []

        # Build key-phrase sets for each finding
        def key_phrases(claim: str) -> Set[str]:
            words = re.findall(r"[a-z0-9][a-z0-9\-\+\.]*[a-z0-9]|[a-z0-9]",
                               claim.lower())
            # Use bigrams + unigrams for better clustering
            unigrams = set(w for w in words if len(w) >= 3)
            bigrams = set(
                f"{words[i]}_{words[i+1]}"
                for i in range(len(words) - 1)
                if len(words[i]) >= 2 and len(words[i + 1]) >= 2
            )
            return unigrams | bigrams

        phrase_sets = [key_phrases(f.get("claim", "")) for f in findings]

        # Greedy clustering
        clusters: List[List[int]] = []  # indices
        assigned: Set[int] = set()

        for i in range(len(findings)):
            if i in assigned:
                continue
            cluster = [i]
            assigned.add(i)
            for j in range(i + 1, len(findings)):
                if j in assigned:
                    continue
                si, sj = phrase_sets[i], phrase_sets[j]
                if not si or not sj:
                    continue
                jaccard = len(si & sj) / len(si | sj)
                if jaccard >= 0.25:
                    cluster.append(j)
                    assigned.add(j)
            clusters.append(cluster)

        return [[findings[idx] for idx in c] for c in clusters]

    # ── Utility ───────────────────────────────────────────────────

    def _list_all_agent_names(self) -> List[str]:
        """Return all agent names from the manifest."""
        if not self.manifest.is_loaded:
            try:
                self.manifest.load()
            except Exception:
                return []
        agents = self.manifest.list_agents()
        return [a.get("name", "") for a in agents if a.get("name")]

    # ── LLM Fine-Ranking (Step 1b) ──────────────────────────────────

    @staticmethod
    def _has_llm_config(llm_config: Any) -> bool:
        """Check if llm_config has a valid API key for LLM calls."""
        if llm_config is None:
            return False
        api_key = getattr(llm_config, "api_key", "") or ""
        return bool(api_key.strip())

    async def _llm_rerank(
        self,
        scored: List[Tuple[str, float, Dict[str, float]]],
        task_text: str,
        metadata: Dict[str, Any],
        llm_config: Any,
    ) -> Tuple[List[Tuple[str, float, Dict[str, float]]], Optional[Dict[str, Any]]]:
        """
        Re-rank top candidates using LLM semantic understanding.

        Takes the top-N from coarse scoring and asks the LLM to rank them
        based on deep semantic match with the task description. Merges LLM
        ranking with coarse scores for final ordering.

        Returns (rescored_list, llm_rerank_info).
        """
        from llm.factory import create_provider
        from llm.base import ChatMessage

        # Take top 15 candidates for LLM evaluation
        top_n = min(15, len(scored))
        candidates = scored[:top_n]
        remaining = scored[top_n:]

        # Build candidate descriptions
        candidate_lines = []
        for i, (name, score, breakdown) in enumerate(candidates):
            agent = self.manifest.get_agent(name) or {}
            desc = agent.get("description", "")[:200]
            domain = agent.get("domain", "unknown")
            caps = ", ".join(agent.get("capabilities", [])[:5])
            expertise = ", ".join(agent.get("expertise_areas", [])[:5])
            candidate_lines.append(
                f"{i+1}. **{name}** (domain: {domain}, coarse_score: {score:.3f})\n"
                f"   Description: {desc}\n"
                f"   Capabilities: {caps}\n"
                f"   Expertise: {expertise}"
            )

        candidates_text = "\n\n".join(candidate_lines)

        system_prompt = (
            "You are an expert task routing system for automotive software engineering. "
            "Your job is to re-rank agent candidates for a given task based on deep semantic fit. "
            "Consider: domain relevance, capability match, required expertise, and the specific "
            "automotive standards mentioned in the task.\n\n"
            "Return a JSON object with:\n"
            '  - "ranking": list of candidate indices (0-based) in best-to-worst order\n'
            '  - "reasoning": brief explanation of the top choice\n'
            '  - "confidence": float 0.0-1.0 for the overall ranking quality\n\n'
            "Respond with ONLY the JSON object, no other text."
        )

        user_prompt = (
            f"## Task\n{task_text[:3000]}\n\n"
            f"## Detected Domains\n{', '.join(metadata.get('detected_domains', []))}\n\n"
            f"## Candidates to Re-Rank\n{candidates_text}\n\n"
            f"Re-rank these {len(candidates)} candidates from best to worst match. "
            f"Return JSON only."
        )

        try:
            provider = create_provider(
                provider=llm_config.provider,
                api_key=llm_config.api_key,
                model=llm_config.model,
                base_url=llm_config.base_url or None,
                temperature=0.1,
                max_tokens=1024,
            )

            response = await provider.chat([
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ])

            try:
                await provider.close()
            except Exception:
                pass

            # Parse JSON response
            import json as _json
            content = response.content.strip()
            # Remove markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
            result = _json.loads(content)

            ranking = result.get("ranking", [])
            confidence = result.get("confidence", 0.5)
            reasoning = result.get("reasoning", "")

            # Build re-ranked list: LLM order first, then merge with coarse scores
            reranked = []
            seen = set()

            # Add LLM-ranked candidates with adjusted scores
            for rank_idx, candidate_idx in enumerate(ranking):
                if 0 <= candidate_idx < len(candidates):
                    name, score, breakdown = candidates[candidate_idx]
                    seen.add(candidate_idx)
                    # Blend: 60% LLM rank position + 40% coarse score
                    rank_boost = 1.0 - (rank_idx / max(len(ranking), 1))
                    blended_score = 0.6 * rank_boost + 0.4 * score
                    # Add LLM reasoning to breakdown
                    breakdown = dict(breakdown)
                    breakdown["llm_rank"] = rank_idx + 1
                    breakdown["llm_confidence"] = confidence
                    reranked.append((name, round(blended_score, 4), breakdown))

            # Add remaining candidates that LLM didn't mention
            for i, (name, score, breakdown) in enumerate(candidates):
                if i not in seen:
                    breakdown = dict(breakdown)
                    breakdown["llm_rank"] = -1
                    reranked.append((name, score, breakdown))

            # Append the remaining (outside top-N)
            reranked.extend(remaining)

            # Sort by blended score
            reranked.sort(key=lambda x: -x[1])

            llm_info = {
                "model": llm_config.model,
                "confidence": confidence,
                "reasoning": reasoning,
                "candidates_reranked": len(candidates),
            }

            return reranked, llm_info

        except Exception as e:
            logger.warning(f"LLM re-rank failed: {e}")
            raise
