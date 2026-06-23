import json
import os
from typing import Optional, List, Dict, Any


class ManifestReader:
    """
    Reads and queries the agent_skill_manifest.json file.
    Maps agents to their domains, capabilities, required skills, and tool dependencies.
    """

    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self._data: Dict[str, Any] = {}
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load the manifest JSON file into memory."""
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self._agents = self._data.get("agents", {})
        self._loaded = True

    def reload(self) -> None:
        """Force reload the manifest from disk."""
        self._loaded = False
        self._data = {}
        self._agents = {}
        self.load()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """Return full agent definition by name."""
        if not self._loaded:
            self.load()
        return self._agents.get(name)

    def get_agent_skills(self, name: str) -> List[str]:
        """Return the list of required skill YAML paths for a given agent."""
        agent = self.get_agent(name)
        if agent is None:
            return []
        raw_skills = agent.get("required_skills", [])
        paths = []
        for skill in raw_skills:
            if isinstance(skill, str):
                paths.append(skill)
            elif isinstance(skill, dict):
                paths.append(skill.get("path", ""))
        return paths

    def get_agent_capabilities(self, name: str) -> List[str]:
        """Return the list of capability tags for a given agent."""
        agent = self.get_agent(name)
        if agent is None:
            return []
        return agent.get("capabilities", [])

    def get_agent_domain(self, name: str) -> str:
        """Return the domain string for a given agent."""
        agent = self.get_agent(name)
        if agent is None:
            return ""
        return agent.get("domain", "")

    def get_agent_tool_dependencies(self, name: str) -> List[str]:
        """Return the list of tool dependencies for a given agent."""
        agent = self.get_agent(name)
        if agent is None:
            return []
        return agent.get("tool_dependencies", [])

    def list_domains(self) -> List[str]:
        """Return all unique domains present in the manifest."""
        if not self._loaded:
            self.load()
        return sorted(list({a.get("domain", "") for a in self._agents.values() if a.get("domain")}))

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return all agents with rich metadata."""
        if not self._loaded:
            self.load()
        result = []
        for name, info in self._agents.items():
            agent = dict(info)
            agent.setdefault("name", name)
            agent.setdefault("description", agent.get("description", ""))
            agent.setdefault("domain", agent.get("domain", "unknown"))
            agent.setdefault("capability_count", len(agent.get("capabilities", [])))
            agent.setdefault("skill_count", len(agent.get("required_skills", [])))
            agent.setdefault("tool_count", len(agent.get("tool_dependencies", [])))
            result.append(agent)
        result.sort(key=lambda a: a.get("name", ""))
        return result

    def list_agents_by_domain(self, domain: str) -> List[str]:
        """Return agent names filtered by domain."""
        if not self._loaded:
            self.load()
        return sorted([
            name for name, info in self._agents.items()
            if info.get("domain") == domain
        ])

    def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """
        Fuzzy search across agent names, domains, capabilities, and tools.
        Returns a list of matching agent dicts with a `match_score` field.
        """
        if not self._loaded:
            self.load()

        query_lower = query.lower()
        query_tokens = query_lower.split()
        results = []

        for name, info in self._agents.items():
            score = 0
            reasons = []

            # Exact agent name match
            if query_lower in name.lower():
                score += 50
                reasons.append(f"agent name matches '{query}'")

            # Domain match
            domain = info.get("domain", "")
            if query_lower in domain.lower():
                score += 30
                reasons.append(f"domain matches '{query}'")

            # Token-level capability matching
            capabilities = info.get("capabilities", [])
            for cap in capabilities:
                cap_lower = cap.lower()
                for token in query_tokens:
                    if token in cap_lower:
                        score += 10
                        reasons.append(f"capability '{cap}' matches token '{token}'")
                        break

            # Token-level tool matching
            tools = info.get("tool_dependencies", [])
            for tool in tools:
                tool_lower = tool.lower()
                for token in query_tokens:
                    if token in tool_lower:
                        score += 8
                        reasons.append(f"tool '{tool}' matches token '{token}'")
                        break

            if score > 0:
                results.append({
                    **info,
                    "name": name,
                    "match_score": score,
                    "match_reasons": reasons,
                })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results

    def get_agent_file(self, name: str) -> Optional[str]:
        """Return the agent YAML file path from the manifest."""
        agent = self.get_agent(name)
        if agent is None:
            return None
        return agent.get("agent_file")

    def to_dict(self) -> Dict[str, Any]:
        """Return the raw manifest data."""
        if not self._loaded:
            self.load()
        return dict(self._data)
