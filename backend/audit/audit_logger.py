import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path

from shared.models import AuditEvent, AuditEventType


class AuditLogger:
    """
    Persistent audit trail for all agent actions, decisions, and state changes.

    Writes an append-only audit.jsonl file to each project's .autodev/ directory.
    Uses per-project asyncio.Lock to prevent concurrent write corruption.
    """

    def __init__(self, project_manager=None):
        self._project_manager = project_manager
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, project_id: str) -> asyncio.Lock:
        if project_id not in self._locks:
            self._locks[project_id] = asyncio.Lock()
        return self._locks[project_id]

    def _audit_path(self, project_id: str) -> Optional[Path]:
        """Resolve the audit.jsonl path for a project."""
        if self._project_manager:
            root = self._project_manager.get_project_path(project_id)
            if root:
                autodev = Path(root) / ".autodev"
                autodev.mkdir(parents=True, exist_ok=True)
                return autodev / "audit.jsonl"
        return None

    # ── Write ──────────────────────────────────────────────────────────

    async def log_event(
        self,
        project_id: str,
        node_id: str,
        event_type: AuditEventType,
        step_index: int = 0,
        step_name: str = "",
        data: Dict[str, Any] = None,
        actor: str = "system",
    ) -> Optional[AuditEvent]:
        """
        Append an audit event to the project's audit.jsonl.
        Returns the created AuditEvent, or None if the project is unavailable.
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4())[:12],
            project_id=project_id,
            node_id=node_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            step_index=step_index,
            step_name=step_name,
            data=data or {},
            actor=actor,
        )

        audit_path = self._audit_path(project_id)
        if not audit_path:
            return None

        lock = self._get_lock(project_id)
        async with lock:
            line = event.model_dump_json(ensure_ascii=False) + "\n"
            await asyncio.to_thread(self._append_line, str(audit_path), line)

        return event

    @staticmethod
    def _append_line(path: str, line: str) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)

    # ── Read ───────────────────────────────────────────────────────────

    async def get_audit_trail(
        self,
        project_id: str,
        node_id: str = None,
        event_types: List[str] = None,
        time_from: str = None,
        time_to: str = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Read the project's audit.jsonl and return filtered, paginated events.
        """
        audit_path = self._audit_path(project_id)
        if not audit_path or not audit_path.exists():
            return []

        lines = await asyncio.to_thread(self._read_lines, str(audit_path))

        events = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Apply filters
            if node_id and evt.get("node_id") != node_id:
                continue
            if event_types and evt.get("event_type") not in event_types:
                continue
            if time_from and evt.get("timestamp", "") < time_from:
                continue
            if time_to and evt.get("timestamp", "") > time_to:
                continue

            events.append(evt)

        # Sort descending (newest first)
        events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

        return events[offset: offset + limit]

    async def get_node_audit(
        self, project_id: str, node_id: str, limit: int = 200
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a single node."""
        return await self.get_audit_trail(
            project_id, node_id=node_id, limit=limit
        )

    async def get_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get summary statistics: event counts by type, per-node breakdown,
        approval/rejection counts.
        """
        audit_path = self._audit_path(project_id)
        if not audit_path or not audit_path.exists():
            return {
                "project_id": project_id,
                "total_events": 0,
                "event_counts": {},
                "node_summaries": {},
                "approvals": 0,
                "rejections": 0,
            }

        lines = await asyncio.to_thread(self._read_lines, str(audit_path))

        event_counts: Dict[str, int] = {}
        node_events: Dict[str, list] = {}
        approvals = 0
        rejections = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue

            etype = evt.get("event_type", "unknown")
            event_counts[etype] = event_counts.get(etype, 0) + 1

            nid = evt.get("node_id", "")
            if nid not in node_events:
                node_events[nid] = []
            node_events[nid].append(evt)

            if etype == "checkpoint_approved":
                approvals += 1
            elif etype == "checkpoint_rejected":
                rejections += 1

        node_summaries = {}
        for nid, evts in node_events.items():
            node_summaries[nid] = {
                "count": len(evts),
                "first_event": min(e.get("timestamp", "") for e in evts),
                "last_event": max(e.get("timestamp", "") for e in evts),
                "statuses": list(set(
                    e.get("data", {}).get("new") or e.get("data", {}).get("previous", "")
                    for e in evts
                    if e.get("event_type") == "node_status_change"
                )),
            }

        return {
            "project_id": project_id,
            "total_events": sum(event_counts.values()),
            "event_counts": event_counts,
            "node_summaries": node_summaries,
            "approvals": approvals,
            "rejections": rejections,
        }

    @staticmethod
    def _read_lines(path: str) -> List[str]:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
