import os
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path


class SkillLoader:
    """
    Loads and installs agents and their skill dependencies on demand.

    Source directories (local bundle):
      - autodev-studio/agents/<domain>/<agent>.yaml
      - autodev-studio/skills/<category>/<skill>.yaml

    Target: project workspace under:
      - ~/autodev-projects/<project-id>/agents/
      - ~/autodev-projects/<project-id>/skills/
    """

    def __init__(self, reference_skills_dir: str = None,
                 agents_dir: str = None):
        self.reference_dir = Path(reference_skills_dir) if reference_skills_dir else None
        self.agents_dir = Path(agents_dir) if agents_dir else None

    # ── Agent installation ────────────────────────────────────────────────

    def install_agent_to_workspace(
        self, workspace_root: str, agent_name: str, manifest: Any
    ) -> Dict[str, Any]:
        """
        Copy agent YAML + all required skill YAMLs into the project workspace.
        Returns {agent_path, skills_copied, errors}.
        """
        agent_info = manifest.get_agent(agent_name)
        if not agent_info:
            return {"error": f"Agent '{agent_name}' not found in manifest"}

        ws = Path(workspace_root)
        ws.mkdir(parents=True, exist_ok=True)

        errors = []
        skills_copied = 0
        agent_file = None

        # 1. Copy agent YAML
        agent_domain = agent_info.get("domain", "unknown")
        agent_src_path = agent_info.get("agent_file", "")
        agent_dst_dir = ws / "agents" / agent_domain
        agent_dst_dir.mkdir(parents=True, exist_ok=True)

        # Try sources in order: local agents dir → reference project
        copied = self._copy_from_dirs(
            src_rel=agent_src_path,
            dst_dir=str(agent_dst_dir),
            search_dirs=self._get_agent_search_dirs(agent_name, agent_domain),
        )
        if copied:
            agent_file = copied
        else:
            errors.append(f"Agent source not found: {agent_src_path}")

        # 2. Copy required skills
        skill_paths = manifest.get_agent_skills(agent_name)
        skill_dst_dir = ws / "skills"
        skill_dst_dir.mkdir(parents=True, exist_ok=True)

        for sp in skill_paths:
            if isinstance(sp, dict):
                sp = sp.get("path", "")
            if not sp:
                continue
            sp = str(sp)
            dst = skill_dst_dir / sp
            dst.parent.mkdir(parents=True, exist_ok=True)
            if self._copy_from_dirs(
                src_rel=sp,
                dst_dir=str(dst.parent),
                search_dirs=self._get_skill_search_dirs(),
            ):
                skills_copied += 1

        return {
            "agent_name": agent_name,
            "domain": agent_domain,
            "agent_file": agent_file,
            "skills_copied": skills_copied,
            "skills_total": len(skill_paths),
            "errors": errors if errors else None,
        }

    def _get_agent_search_dirs(self, agent_name: str, domain: str) -> List[str]:
        dirs = []
        if self.agents_dir:
            dirs.append(str(self.agents_dir / domain))
            dirs.append(str(self.agents_dir))  # flat search
        # Also search reference project
        ref_agents = self.agents_dir.parent.parent / "参考项目" / "automotive-claude-code-agents-main" / "agents" / domain if self.agents_dir else None
        if ref_agents and ref_agents.exists():
            dirs.append(str(ref_agents))
        return dirs

    def _get_skill_search_dirs(self) -> List[str]:
        dirs = []
        if self.reference_dir:
            dirs.append(str(self.reference_dir))
        return dirs

    def _copy_from_dirs(
        self, src_rel: str, dst_dir: str, search_dirs: List[str]
    ) -> Optional[str]:
        """
        Try to find src_rel in each search_dir, copy to dst_dir.
        Returns the destination path if found, None otherwise.
        """
        fname = os.path.basename(src_rel)
        for search_dir in search_dirs:
            # Try exact relative path first
            candidate = os.path.join(search_dir, fname)
            if os.path.isfile(candidate):
                dst = os.path.join(dst_dir, fname)
                shutil.copy2(candidate, dst)
                return dst
            # Try with relative path structure
            candidate2 = os.path.join(search_dir, src_rel.replace("skills/", "", 1))
            if os.path.isfile(candidate2):
                dst = os.path.join(dst_dir, fname)
                shutil.copy2(candidate2, dst)
                return dst
        return None

    # ── Skill resolution (direct from source directories) ─────────────────

    def resolve_skill_path(self, skill_path: str) -> Optional[str]:
        """
        Find a skill file in the source directories.
        Returns the absolute path if found, None otherwise.
        """
        fname = os.path.basename(skill_path)
        for search_dir in self._get_skill_search_dirs():
            # Try exact relative path
            candidate = os.path.join(search_dir, fname)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
            # Try with relative path structure
            candidate2 = os.path.join(search_dir, skill_path.replace("skills/", "", 1))
            if os.path.isfile(candidate2):
                return os.path.abspath(candidate2)
        return None

    def get_agent_skills(self, agent_name: str, manifest: Any) -> List[str]:
        """
        Resolve all skill paths for an agent directly from source directories.
        Returns absolute paths to skill files (no caching/copying).
        """
        skill_paths = manifest.get_agent_skills(agent_name)
        resolved_paths = []
        for sp in skill_paths:
            if isinstance(sp, dict):
                sp = sp.get("path", "")
            if not sp:
                continue
            resolved = self.resolve_skill_path(str(sp))
            if resolved:
                resolved_paths.append(resolved)
        return resolved_paths
