import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from shared.models import NodeStatus


class CheckpointManager:
    """
    Manages workflow step progress with configurable confirmation points.
    Supports pause-and-resume and chat-at-checkpoint workflows.
    """

    def __init__(self):
        # node_id -> checkpoint state dict
        self._states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def init_node(self, node_id: str, workflow_steps: List[Dict[str, Any]]) -> None:
        """Initialize checkpoint tracking for a node's workflow."""
        async with self._lock:
            self._states[node_id] = {
                "total_steps": len(workflow_steps),
                "current_step": 0,
                "step_results": {},
                "is_paused": False,
                "pause_reason": "",
                "chat_messages": [],
                "pending_confirmation": False,
                "confirmation_data": None,
                "started_at": datetime.utcnow().isoformat(),
                "approval_status": None,  # "pending" | "approved" | "rejected"
                "approval_data": None,    # {decided_by, reason, decided_at}
            }

    async def advance_step(self, node_id: str) -> int:
        """Move to the next step, return new step index (0-based)."""
        async with self._lock:
            state = self._states.get(node_id)
            if state is None:
                return 0
            state["current_step"] += 1
            return state["current_step"]

    async def get_current_step(self, node_id: str) -> int:
        """Get current step index (0-based)."""
        state = self._states.get(node_id)
        if state is None:
            return 0
        return state["current_step"]

    async def get_total_steps(self, node_id: str) -> int:
        """Get total step count."""
        state = self._states.get(node_id)
        if state is None:
            return 0
        return state["total_steps"]

    async def should_pause(self, node_id: str, step_config: Dict[str, Any]) -> bool:
        """
        Determine if execution should pause at this step.
        Pauses at steps with type='checkpoint', confirmation=true, or
        safety_impact 'high'/'critical' (must have human review).
        """
        step_type = step_config.get("type", "automatic")
        requires_confirmation = step_config.get("confirmation", False)
        safety = step_config.get("safety_impact", "low")
        # High/critical safety steps always require a pause even if not explicitly flagged
        if safety in ("high", "critical"):
            return True
        return step_type == "checkpoint" or requires_confirmation

    async def pause(self, node_id: str, reason: str, confirmation_data: Dict[str, Any] = None) -> None:
        """Pause execution at the current step."""
        async with self._lock:
            state = self._states.get(node_id)
            if state is None:
                return
            state["is_paused"] = True
            state["pause_reason"] = reason
            state["pending_confirmation"] = True
            state["confirmation_data"] = confirmation_data

    async def resume(self, node_id: str) -> bool:
        """Resume execution from pause. Returns True if was paused."""
        async with self._lock:
            state = self._states.get(node_id)
            if state is None:
                return False
            was_paused = state["is_paused"]
            state["is_paused"] = False
            state["pause_reason"] = ""
            state["pending_confirmation"] = False
            state["confirmation_data"] = None
            return was_paused

    async def approve(self, node_id: str, decided_by: str = "user", reason: str = "") -> Dict[str, Any]:
        """Approve the current checkpoint. Stores decision and resumes."""
        async with self._lock:
            state = self._states.get(node_id)
            if state is None:
                return {"error": "Node not found"}
            state["approval_status"] = "approved"
            state["approval_data"] = {
                "decided_by": decided_by,
                "reason": reason,
                "decided_at": datetime.utcnow().isoformat(),
            }
            decision = {
                "node_id": node_id,
                "decision": "approved",
                "decided_by": decided_by,
                "reason": reason,
                "decided_at": state["approval_data"]["decided_at"],
            }
            # Also resume
            state["is_paused"] = False
            state["pause_reason"] = ""
            state["pending_confirmation"] = False
            state["confirmation_data"] = None
            return decision

    async def reject(self, node_id: str, decided_by: str = "user", reason: str = "") -> Dict[str, Any]:
        """Reject the current checkpoint. Stores decision."""
        async with self._lock:
            state = self._states.get(node_id)
            if state is None:
                return {"error": "Node not found"}
            state["approval_status"] = "rejected"
            state["approval_data"] = {
                "decided_by": decided_by,
                "reason": reason,
                "decided_at": datetime.utcnow().isoformat(),
            }
            # Unpause so the waiting loop can handle rejection
            state["is_paused"] = False
            state["pause_reason"] = ""
            state["pending_confirmation"] = False
            state["confirmation_data"] = None
            return {
                "node_id": node_id,
                "decision": "rejected",
                "decided_by": decided_by,
                "reason": reason,
                "decided_at": state["approval_data"]["decided_at"],
            }

    async def get_approval_status(self, node_id: str) -> Optional[str]:
        """Get the current approval status: None, 'pending', 'approved', or 'rejected'."""
        state = self._states.get(node_id)
        if state is None:
            return None
        return state.get("approval_status")

    async def is_paused(self, node_id: str) -> bool:
        """Check if node execution is paused."""
        state = self._states.get(node_id)
        if state is None:
            return False
        return state["is_paused"]

    async def add_chat_message(self, node_id: str, role: str, content: str) -> None:
        """Add a chat message during a checkpoint pause."""
        async with self._lock:
            state = self._states.get(node_id)
            if state is None:
                return
            state["chat_messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            })

    async def get_chat_history(self, node_id: str) -> List[Dict[str, str]]:
        """Get the chat history for a paused node."""
        state = self._states.get(node_id)
        if state is None:
            return []
        return list(state["chat_messages"])

    async def record_step_result(self, node_id: str, step_index: int, result: Dict[str, Any]) -> None:
        """Record the output of a completed workflow step."""
        async with self._lock:
            state = self._states.get(node_id)
            if state is None:
                return
            state["step_results"][str(step_index)] = result

    async def get_step_result(self, node_id: str, step_index: int) -> Optional[Dict[str, Any]]:
        """Get the result of a specific workflow step."""
        state = self._states.get(node_id)
        if state is None:
            return None
        return state["step_results"].get(str(step_index))

    async def get_all_results(self, node_id: str) -> Dict[str, Any]:
        """Get all step results for a node."""
        state = self._states.get(node_id)
        if state is None:
            return {}
        return dict(state["step_results"])

    async def is_pending_confirmation(self, node_id: str) -> bool:
        """Check if waiting for user confirmation."""
        state = self._states.get(node_id)
        if state is None:
            return False
        return state["pending_confirmation"]

    async def get_confirmation_data(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get the data for the current confirmation prompt."""
        state = self._states.get(node_id)
        if state is None:
            return None
        return state["confirmation_data"]

    async def cleanup(self, node_id: str) -> None:
        """Remove checkpoint state for a completed/cancelled node."""
        async with self._lock:
            if node_id in self._states:
                del self._states[node_id]

    def get_state_snapshot(self, node_id: str) -> Dict[str, Any]:
        """Get a snapshot of the current checkpoint state (non-async for status queries)."""
        state = self._states.get(node_id)
        if state is None:
            return {}
        return {
            "current_step": state["current_step"],
            "total_steps": state["total_steps"],
            "is_paused": state["is_paused"],
            "pause_reason": state["pause_reason"],
            "pending_confirmation": state["pending_confirmation"],
        }
