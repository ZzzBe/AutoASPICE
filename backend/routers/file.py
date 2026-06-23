"""
File management router - upload, read, save, list files.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
import os
import base64
import logging

from shared.models import FileContent, FileListResponse, FileItem
from shared.state import get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


def _get_project_mgr():
    mgr = get_service("project_manager")
    if mgr is None:
        raise HTTPException(status_code=500, detail="Project manager not initialized")
    return mgr


@router.post("/upload")
async def upload_file(
    project_id: str = Form(...),
    file_name: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
):
    """Upload a file to a project directory. Accepts base64 content."""
    project_mgr = _get_project_mgr()

    project = project_mgr.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not content:
        raise HTTPException(status_code=400, detail="No content provided")

    if not file_name:
        file_name = "uploaded_file"

    # Decode base64 content
    try:
        file_data = base64.b64decode(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    success = project_mgr.upload_file(project_id, file_name, file_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to write file")

    dest_path = os.path.join(project.root_path, file_name)
    return {
        "status": "uploaded",
        "path": dest_path,
        "name": file_name,
        "size": len(file_data),
    }


@router.get("/read")
async def read_file(project_id: str, path: str = ""):
    """Read a file's content from a project."""
    project_mgr = _get_project_mgr()

    content = project_mgr.read_file(project_id, path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or not readable")

    full_path = os.path.join(project_mgr.get_project_path(project_id) or "", path)
    file_size = len(content.encode("utf-8", errors="replace"))

    # Determine if the content is likely base64 (binary file)
    try:
        content.encode("ascii")
        is_binary = False
    except UnicodeEncodeError:
        is_binary = True

    return {
        "path": full_path,
        "name": os.path.basename(path),
        "content": content,
        "size": file_size,
        "is_binary": is_binary,
    }


@router.post("/save")
async def save_file(data: FileContent):
    """Save content to a file within a project."""
    project_mgr = _get_project_mgr()

    # path is relative to project; extract project_id from path or query param
    # Full path format: project_id/relative_path
    file_path = data.path

    # Try to infer project_id from path
    parts = file_path.replace("\\", "/").lstrip("/").split("/", 1)
    project_id = parts[0]
    rel_path = parts[1] if len(parts) > 1 else file_path

    success = project_mgr.write_file(project_id, rel_path, data.content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to write file")

    full_path = os.path.join(project_mgr.get_project_path(project_id) or "", rel_path)
    return {
        "status": "saved",
        "path": full_path,
        "size": os.path.getsize(full_path) if os.path.exists(full_path) else len(data.content),
    }


@router.get("/list", response_model=FileListResponse)
async def list_files(project_id: str):
    """List all files in a project directory."""
    project_mgr = _get_project_mgr()

    project = project_mgr.get_project(project_id)
    if not project:
        return FileListResponse(files=[], project_id=project_id)

    project_path = project.root_path
    items = []

    if not os.path.exists(project_path):
        return FileListResponse(files=[], project_id=project_id)

    for root, dirs, filenames in os.walk(project_path):
        # Skip hidden directories (except .autodev)
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".autodev"]

        for fname in filenames:
            if fname.startswith(".") and not fname.startswith(".autodev"):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, project_path)
            _, ext = os.path.splitext(fname)
            try:
                fsize = os.path.getsize(full_path)
            except OSError:
                fsize = 0
            items.append(FileItem(
                name=fname,
                path=full_path,
                relative_path=rel_path,
                extension=ext,
                size=fsize,
                is_dir=False,
            ))

        for dname in dirs:
            full_path = os.path.join(root, dname)
            rel_path = os.path.relpath(full_path, project_path)
            items.append(FileItem(
                name=dname,
                path=full_path,
                relative_path=rel_path,
                extension="",
                size=0,
                is_dir=True,
            ))

    return FileListResponse(files=items, project_id=project_id)
