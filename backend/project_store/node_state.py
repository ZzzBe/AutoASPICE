from typing import Dict, Optional
from datetime import datetime

from shared.models import NodeStatus


class NodeStateManager:
    """
    Manages agent node state transitions in memory.
    Enforces the valid state machine:
      pending -> running -> completed / failed / cancelled
      running -> paused -> running

    This is an in-memory store. In production, this would be backed by
    the project JSON file for persistence across restarts.
    """

    def __init__(self):
        # node_id -> current NodeStatus
        self._states: Dict[str, NodeStatus] = {}
        # node_id -> completed_at timestamp
        self._completed_at: Dict[str, Optional[str]] = {}

    def register(self, node_id: str, initial_status: NodeStatus = NodeStatus.PENDING) -> None:
        """Register a new node with an initial status."""
        self._states[node_id] = initial_status
        self._completed_at[node_id] = None

    def transition(self, node_id: str, target: NodeStatus) -> bool:
        """
        Attempt to transition a node to a target status.
        Validates the transition against the state machine.
        Returns True if the transition is valid and was applied.
        """
        current = self._states.get(node_id, NodeStatus.PENDING)

        # Define valid transitions
        valid_transitions = {
            NodeStatus.PENDING: {NodeStatus.RUNNING, NodeStatus.CANCELLED},
            NodeStatus.RUNNING: {
                NodeStatus.COMPLETED, NodeStatus.FAILED,
                NodeStatus.CANCELLED, NodeStatus.PAUSED,
            },
            NodeStatus.PAUSED: {NodeStatus.RUNNING, NodeStatus.CANCELLED},
            NodeStatus.COMPLETED: set(),    # Terminal state
            NodeStatus.FAILED: set(),       # Terminal state
            NodeStatus.CANCELLED: set(),    # Terminal state
        }

        allowed = valid_transitions.get(current, set())

        if target not in allowed:
            # Allow forcing to FAILED or CANCELLED from any state for cleanup
            if target in (NodeStatus.FAILED, NodeStatus.CANCELLED):
                self._states[node_id] = target
                if target in (NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.CANCELLED):
                    self._completed_at[node_id] = datetime.utcnow().isoformat()
                return True
            return False

        self._states[node_id] = target

        # Set completion timestamp for terminal states
        if target in (NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.CANCELLED):
            if not self._completed_at.get(node_id):
                self._completed_at[node_id] = datetime.utcnow().isoformat()

        return True

    def get_status(self, node_id: str) -> NodeStatus:
        """Get the current status of a node."""
        return self._states.get(node_id, NodeStatus.PENDING)

    def get_completed_at(self, node_id: str) -> Optional[str]:
        """Get the completed_at timestamp for a node."""
        return self._completed_at.get(node_id)

    def set_completed_at(self, node_id: str, timestamp: str) -> None:
        """Set the completed_at timestamp."""
        self._completed_at[node_id] = timestamp

    def is_terminal(self, node_id: str) -> bool:
        """Check if a node is in a terminal state."""
        return self._states.get(node_id) in (
            NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.CANCELLED
        )

    def is_running(self, node_id: str) -> bool:
        """Check if a node is currently running."""
        return self._states.get(node_id) == NodeStatus.RUNNING

    def is_paused(self, node_id: str) -> bool:
        """Check if a node is paused."""
        return self._states.get(node_id) == NodeStatus.PAUSED

    def remove(self, node_id: str) -> None:
        """Remove a node's state tracking."""
        self._states.pop(node_id, None)
        self._completed_at.pop(node_id, None)

    def get_all_states(self) -> Dict[str, NodeStatus]:
        """Get all tracked node states."""
        return dict(self._states)
