"""
Shared application state module.
Holds references to backend service singletons so routers can access them
without circular imports. Populated by main.py during application startup.
"""
from typing import Dict, Any, Optional

# Dictionary of service instances: {"output_stream": ..., "agent_runtime": ..., ...}
app_state: Dict[str, Any] = {}


def get_service(name: str) -> Optional[Any]:
    """Get a service by name from app state."""
    return app_state.get(name)


def set_service(name: str, instance: Any) -> None:
    """Register a service in app state."""
    app_state[name] = instance
