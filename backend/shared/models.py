from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AuditEventType(str, Enum):
    NODE_CREATED = "node_created"
    NODE_STATUS_CHANGE = "node_status_change"
    STEP_START = "step_start"
    STEP_END = "step_end"
    STEP_OUTPUT = "step_output"
    CHECKPOINT_REACHED = "checkpoint_reached"
    CHECKPOINT_CHAT = "checkpoint_chat"
    CHECKPOINT_APPROVED = "checkpoint_approved"
    CHECKPOINT_REJECTED = "checkpoint_rejected"
    EXECUTION_COMPLETE = "execution_complete"
    EXECUTION_ERROR = "execution_error"


class SafetyImpact(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    project_id: str
    node_id: str
    event_type: AuditEventType
    timestamp: str = ""
    step_index: int = 0
    step_name: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    actor: str = "system"


class ApprovalDecision(BaseModel):
    node_id: str
    step_index: int = 0
    step_name: str = ""
    decided_by: str = "user"
    decided_at: str = ""
    decision: str = ""  # "approved" | "rejected"
    reason: str = ""
    step_output_preview: Dict[str, Any] = Field(default_factory=dict)


class AgentNode(BaseModel):
    id: str
    agent_name: str
    domain: str
    status: NodeStatus = NodeStatus.PENDING
    workflow_steps: List[Dict[str, Any]] = []
    current_step: int = 0
    total_steps: int = 0
    deliverables: List[str] = []
    context_files: List[str] = []
    created_at: str = ""
    completed_at: Optional[str] = None
    output_log: List[Dict[str, Any]] = []


class Project(BaseModel):
    id: str
    name: str
    root_path: str
    nodes: List[AgentNode] = []
    created_at: str = ""
    updated_at: str = ""


class RoutingRequest(BaseModel):
    text_instruction: str = ""
    uploaded_files: List[str] = []
    file_contents: Dict[str, str] = {}


class AgentSuggestion(BaseModel):
    agent_name: str
    domain: str
    confidence: float
    reason: str
    required_skills: List[str] = []


class RoutingResponse(BaseModel):
    suggestions: List[AgentSuggestion] = []


class LLMConfigRequest(BaseModel):
    """LLM configuration sent from frontend with each agent execution."""
    provider: str = "openai"  # openai | anthropic | deepseek | google | custom
    api_key: str = ""
    model: str = "gpt-4o"
    base_url: str = ""


class ExecuteAgentRequest(BaseModel):
    project_id: str
    node_id: str
    agent_name: str
    context_files: List[str] = []
    user_instruction: str = ""
    llm_config: LLMConfigRequest = Field(default_factory=LLMConfigRequest)


class AgentMessage(BaseModel):
    type: str  # "output", "step_start", "step_end", "checkpoint", "error", "done"
    node_id: str
    data: Dict[str, Any] = {}


# Request models for project creation and node management
class CreateProjectRequest(BaseModel):
    name: str
    root_path: str = ""


class AddNodeRequest(BaseModel):
    agent_name: str
    domain: str
    workflow_steps: List[Dict[str, Any]] = []
    context_files: List[str] = []


# File management models
class FileContent(BaseModel):
    path: str
    content: str


class FileItem(BaseModel):
    name: str
    path: str
    relative_path: str
    extension: str
    size: int
    is_dir: bool = False


class FileListResponse(BaseModel):
    files: List[FileItem] = []
    project_id: str


# ── AgentRouter models ────────────────────────────────────────────

class FanOutSubTask(BaseModel):
    """A single sub-task dispatched to a specific agent in a fan-out plan."""
    sub_task_id: str
    description: str
    agent_name: str
    domain: str
    confidence: float
    required_tools: List[str] = []
    input_context: Dict[str, Any] = Field(default_factory=dict)


class ConsensusResult(BaseModel):
    """Aggregated output from 3-5 parallel expert agents after consensus building."""
    agreed_findings: List[Dict[str, Any]] = Field(default_factory=list)
    disagreements: List[Dict[str, Any]] = Field(default_factory=list)
    unique_insights: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = 0.0
    requires_human_review: bool = False
    participant_agents: List[str] = Field(default_factory=list)


class RouterResult(BaseModel):
    """Full routing analysis result from the AgentRouter."""
    suggestions: List[AgentSuggestion] = Field(default_factory=list)
    fan_out_plan: List[FanOutSubTask] = Field(default_factory=list)
    detected_domains: List[str] = Field(default_factory=list)
    parsed_metadata: Dict[str, Any] = Field(default_factory=dict)


class RoutingRequestEnhanced(RoutingRequest):
    """Extended routing request with user preferences and execution hints."""
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preferred agents, past history, and user-specified constraints"
    )
    require_consensus: bool = Field(
        default=False,
        description="When True, fan-out to multiple agents and build consensus"
    )
    max_parallel_agents: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of parallel agents for fan-out"
    )
    llm_config: Optional[LLMConfigRequest] = Field(
        default=None,
        description="Optional LLM config for fine-grained re-ranking (Step 1b)"
    )


class ConsensusRequest(BaseModel):
    """Request to build consensus from parallel agent outputs."""
    task_description: str = ""
    agent_outputs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {agent_name, domain, findings: [...]} from parallel agents"
    )
    min_agreement_threshold: int = Field(
        default=2,
        description="Minimum number of agents that must agree for a finding to be 'agreed'"
    )
