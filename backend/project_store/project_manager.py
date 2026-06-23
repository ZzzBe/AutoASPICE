import json
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from shared.models import Project, AgentNode, NodeStatus


class ProjectManager:
    """
    Filesystem-based project storage.
    Each project is a directory containing a .autodev/project.json metadata file
    and node subdirectories for agent deliverables.
    """

    def __init__(self, projects_root: str):
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(parents=True, exist_ok=True)
        # In-memory cache of project data
        self._cache: Dict[str, Project] = {}

    # ------------------------------------------------------------------
    # Project CRUD
    # ------------------------------------------------------------------

    def create_project(self, name: str, project_id: str = None) -> Project:
        """
        Create a new project directory with .autodev/project.json metadata.
        Returns the created Project object.
        """
        if project_id is None:
            project_id = str(uuid.uuid4())[:8]

        project_dir = self.projects_root / project_id
        autodev_dir = project_dir / ".autodev"

        # Ensure unique directory
        if project_dir.exists():
            raise FileExistsError(f"Project directory already exists: {project_dir}")

        project_dir.mkdir(parents=True)
        autodev_dir.mkdir()

        now = datetime.utcnow().isoformat()

        project = Project(
            id=project_id,
            name=name,
            root_path=str(project_dir),
            nodes=[],
            created_at=now,
            updated_at=now,
        )

        self._save_project_json(project)
        self._cache[project_id] = project
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID. Loads from cache or filesystem.
        """
        if project_id in self._cache:
            return self._cache[project_id]

        project = self._load_project_json(project_id)
        if project:
            self._cache[project_id] = project
        return project

    def list_projects(self) -> List[Project]:
        """
        List all projects found under the projects root.
        """
        projects = []
        if not self.projects_root.exists():
            return projects

        for entry in self.projects_root.iterdir():
            if entry.is_dir():
                autodev_dir = entry / ".autodev"
                if autodev_dir.exists():
                    project = self._load_project_json(entry.name)
                    if project:
                        projects.append(project)
                        self._cache[entry.name] = project
        return projects

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project directory and all its contents.
        Returns True if successful.
        """
        project_dir = self.projects_root / project_id
        if not project_dir.exists():
            return False

        shutil.rmtree(str(project_dir))
        self._cache.pop(project_id, None)
        return True

    def update_project(self, project_id: str, **kwargs) -> Optional[Project]:
        """
        Update project metadata fields.
        """
        project = self.get_project(project_id)
        if project is None:
            return None

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updated_at = datetime.utcnow().isoformat()
        self._save_project_json(project)
        self._cache[project_id] = project
        return project

    # ------------------------------------------------------------------
    # Node Management
    # ------------------------------------------------------------------

    def add_node(self, project_id: str, node: AgentNode) -> Optional[AgentNode]:
        """
        Add an agent node to a project. Creates a node subdirectory.
        """
        project = self.get_project(project_id)
        if project is None:
            return None

        # Assign ID if not set
        if not node.id:
            node.id = str(uuid.uuid4())[:8]

        # Set timestamps
        if not node.created_at:
            node.created_at = datetime.utcnow().isoformat()

        # Create node subdirectory
        node_dir = self._get_node_dir(project_id, node.id)
        node_dir.mkdir(parents=True, exist_ok=True)

        project.nodes.append(node)
        project.updated_at = datetime.utcnow().isoformat()
        self._save_project_json(project)
        self._cache[project_id] = project
        return node

    def get_node(self, project_id: str, node_id: str) -> Optional[AgentNode]:
        """
        Get a specific node from a project.
        """
        project = self.get_project(project_id)
        if project is None:
            return None

        for node in project.nodes:
            if node.id == node_id:
                return node
        return None

    def update_node(
        self, project_id: str, node_id: str, **kwargs
    ) -> Optional[AgentNode]:
        """
        Update fields of a specific agent node.
        """
        project = self.get_project(project_id)
        if project is None:
            return None

        for node in project.nodes:
            if node.id == node_id:
                for key, value in kwargs.items():
                    if hasattr(node, key):
                        setattr(node, key, value)
                project.updated_at = datetime.utcnow().isoformat()
                self._save_project_json(project)
                self._cache[project_id] = project
                return node
        return None

    def remove_node(self, project_id: str, node_id: str) -> bool:
        """
        Remove an agent node from a project. Optionally removes its directory.
        """
        project = self.get_project(project_id)
        if project is None:
            return False

        for i, node in enumerate(project.nodes):
            if node.id == node_id:
                project.nodes.pop(i)
                project.updated_at = datetime.utcnow().isoformat()

                # Remove node directory
                node_dir = self._get_node_dir(project_id, node_id)
                if node_dir.exists():
                    shutil.rmtree(str(node_dir))

                self._save_project_json(project)
                self._cache[project_id] = project
                return True
        return False

    def list_nodes(self, project_id: str) -> List[AgentNode]:
        """
        List all nodes in a project.
        """
        project = self.get_project(project_id)
        if project is None:
            return []
        return list(project.nodes)

    # ------------------------------------------------------------------
    # File Operations
    # ------------------------------------------------------------------

    def get_project_path(self, project_id: str) -> Optional[str]:
        """Get the absolute filesystem path for a project."""
        project = self.get_project(project_id)
        if project is None:
            return None
        return project.root_path

    def get_node_path(self, project_id: str, node_id: str) -> Optional[str]:
        """Get the absolute filesystem path for a node's directory."""
        node = self.get_node(project_id, node_id)
        if node is None:
            return None
        node_dir = self._get_node_dir(project_id, node_id)
        return str(node_dir)

    def list_project_files(self, project_id: str) -> List[str]:
        """
        List all files in the project directory (relative paths).
        Excludes .autodev directory.
        """
        project_dir = self.projects_root / project_id
        if not project_dir.exists():
            return []

        files = []
        for root, _, filenames in os.walk(project_dir):
            if ".autodev" in root.split(os.sep):
                continue
            for f in filenames:
                full_path = Path(root) / f
                rel_path = full_path.relative_to(project_dir)
                files.append(str(rel_path))
        return sorted(files)

    def read_file(self, project_id: str, file_path: str) -> Optional[str]:
        """
        Read the content of a file within a project directory.
        file_path is relative to the project root.
        """
        project = self.get_project(project_id)
        if project is None:
            return None

        full_path = Path(project.root_path) / file_path

        # Security: ensure the resolved path is within the project directory
        try:
            full_path.resolve().relative_to(Path(project.root_path).resolve())
        except ValueError:
            return None  # Path traversal attempt

        if not full_path.exists() or not full_path.is_file():
            return None

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try binary read for non-text files
            try:
                with open(full_path, "rb") as f:
                    return f.read().decode("latin-1")
            except Exception:
                return None
        except Exception:
            return None

    def write_file(self, project_id: str, file_path: str, content: str) -> bool:
        """
        Write content to a file within a project directory.
        Creates parent directories if needed.
        """
        project = self.get_project(project_id)
        if project is None:
            return False

        full_path = Path(project.root_path) / file_path

        # Security check
        try:
            full_path.resolve().relative_to(Path(project.root_path).resolve())
        except ValueError:
            return False

        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def upload_file(
        self, project_id: str, file_path: str, content: bytes
    ) -> bool:
        """
        Upload a file (binary content) to a project directory.
        """
        project = self.get_project(project_id)
        if project is None:
            return False

        full_path = Path(project.root_path) / file_path

        try:
            full_path.resolve().relative_to(Path(project.root_path).resolve())
        except ValueError:
            return False

        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(full_path, "wb") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def get_node_dir(self, project_id: str, node_id: str) -> str:
        """Get the node directory path as a string."""
        return str(self._get_node_dir(project_id, node_id))

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _get_node_dir(self, project_id: str, node_id: str) -> Path:
        """Get the Path to a node's subdirectory."""
        node = self.get_node(project_id, node_id)
        if node:
            safe_name = node.agent_name.replace(" ", "_").lower()
        else:
            safe_name = "unnamed"
        # Ensure uniqueness if multiple nodes share agent name
        return self.projects_root / project_id / f"{node_id}-{safe_name}"

    def _save_project_json(self, project: Project) -> None:
        """Serialize project metadata to .autodev/project.json."""
        autodev_dir = Path(project.root_path) / ".autodev"
        autodev_dir.mkdir(parents=True, exist_ok=True)

        project_json = autodev_dir / "project.json"
        with open(project_json, "w", encoding="utf-8") as f:
            json.dump(project.model_dump(), f, indent=2, ensure_ascii=False)

    def _load_project_json(self, project_id: str) -> Optional[Project]:
        """Load project metadata from .autodev/project.json."""
        project_json = self.projects_root / project_id / ".autodev" / "project.json"
        if not project_json.exists():
            return None

        try:
            with open(project_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            project = Project(**data)
            # Ensure root_path is absolute
            if not Path(project.root_path).is_absolute():
                project.root_path = str(self.projects_root / project_id)
            return project
        except Exception:
            return None
