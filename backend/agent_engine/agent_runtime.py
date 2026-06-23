import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

from shared.models import NodeStatus, AgentNode, ExecuteAgentRequest, AuditEventType
from agent_engine.output_stream import OutputStreamManager
from agent_engine.manifest import ManifestReader
from agent_engine.skill_loader import SkillLoader
from agent_engine.step_checkpoint import CheckpointManager
from sdk_adapter.sdk_client import SDKClient
from sdk_adapter.yaml_converter import YAMLConverter
from project_store.node_state import NodeStateManager


class AgentRuntime:
    """
    Manages the full lifecycle of agent execution.
    Coordinates between the SDK client, checkpoint manager, output stream,
    skill loader, and node state manager for background task execution.
    """

    def __init__(
        self,
        manifest: ManifestReader,
        skill_loader: SkillLoader,
        sdk_client: SDKClient,
        output_stream: OutputStreamManager,
        node_state: NodeStateManager,
        audit_logger: "AuditLogger" = None,
        project_manager: "ProjectManager" = None,
    ):
        self.manifest = manifest
        self.skill_loader = skill_loader
        self.sdk_client = sdk_client
        self.output_stream = output_stream
        self.checkpoint_mgr = CheckpointManager()
        self.node_state = node_state
        self.audit_logger = audit_logger
        self.project_manager = project_manager
        # Track active tasks: node_id -> asyncio.Task
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_lock = asyncio.Lock()

    def submit_task(
        self,
        request: ExecuteAgentRequest,
        workflow_steps: List[Dict[str, Any]],
    ) -> asyncio.Task:
        """
        Submit an agent execution request as an async background task.
        Returns the asyncio.Task for tracking.
        """
        task = asyncio.create_task(
            self._execute(request, workflow_steps),
            name=f"agent-{request.node_id}"
        )
        # Store task reference
        asyncio.ensure_future(self._register_task(request.node_id, task))
        return task

    async def _register_task(self, node_id: str, task: asyncio.Task) -> None:
        async with self._task_lock:
            self._active_tasks[node_id] = task

    async def _log_audit(
        self, project_id: str, node_id: str, event_type: AuditEventType,
        step_index: int = 0, step_name: str = "", data: dict = None,
        actor: str = "system",
    ):
        """Emit an audit event if audit_logger is available."""
        if not self.audit_logger:
            return
        try:
            await self.audit_logger.log_event(
                project_id=project_id, node_id=node_id,
                event_type=event_type, step_index=step_index,
                step_name=step_name, data=data or {}, actor=actor,
            )
        except Exception:
            pass  # Audit failures should never break execution

    async def _populate_output_log(
        self, project_id: str, node_id: str, step_index: int,
        step_name: str, step_result: dict,
    ):
        """Append step output to the AgentNode.output_log and persist."""
        if not self.project_manager:
            return
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                return
            for node in project.nodes:
                if node.id == node_id:
                    entry = {
                        "step_index": step_index,
                        "step_name": step_name,
                        "result": step_result,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    node.output_log.append(entry)
                    self.project_manager._save_project_json(project)
                    break
        except Exception:
            pass

    async def _execute(
        self,
        request: ExecuteAgentRequest,
        workflow_steps: List[Dict[str, Any]],
    ) -> None:
        """
        Main execution loop for an agent node.
        Runs through workflow steps, handling checkpoints and streaming output.
        Emits audit events at every lifecycle transition.
        """
        node_id = request.node_id
        agent_name = request.agent_name
        pid = request.project_id

        try:
            # Mark node as running
            self.node_state.transition(node_id, NodeStatus.RUNNING)
            await self.output_stream.set_active(node_id, True)

            await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                data={"previous": "pending", "new": "running"},
                actor=f"agent:{agent_name}")

            # Initialize checkpoint tracking
            await self.checkpoint_mgr.init_node(node_id, workflow_steps)

            # Resolve agent skills from source directories
            skill_paths = self.skill_loader.get_agent_skills(agent_name, self.manifest)

            await self.output_stream.push(node_id, "output", {
                "text": f"Agent '{agent_name}' starting execution...",
                "timestamp": datetime.utcnow().isoformat(),
            })
            await self.output_stream.push(node_id, "output", {
                "text": f"Loaded {len(skill_paths)} skill(s)",
                "timestamp": datetime.utcnow().isoformat(),
            })
            await self.output_stream.push(node_id, "output", {
                "text": f"Workflow has {len(workflow_steps)} step(s)",
                "timestamp": datetime.utcnow().isoformat(),
            })

            total_steps = len(workflow_steps)

            for step_index, step_config in enumerate(workflow_steps):
                # Check if cancelled
                status = self.node_state.get_status(node_id)
                if status == NodeStatus.CANCELLED:
                    await self.output_stream.push(node_id, "output", {
                        "text": "Execution cancelled by user.",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    break

                step_name = step_config.get("name", f"Step {step_index + 1}")
                step_type = step_config.get("type", "automatic")

                # Audit: step start
                await self._log_audit(pid, node_id, AuditEventType.STEP_START,
                    step_index=step_index, step_name=step_name,
                    data={"step_type": step_type, "total_steps": total_steps},
                    actor=f"agent:{agent_name}")

                # Announce step start
                await self.output_stream.push(node_id, "step_start", {
                    "step_index": step_index,
                    "step_name": step_name,
                    "step_type": step_type,
                    "total_steps": total_steps,
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # Advance checkpoint
                await self.checkpoint_mgr.advance_step(node_id)

                # Execute the step via SDK client
                try:
                    step_result = await self.sdk_client.execute_step(
                        agent_name=agent_name,
                        step_config=step_config,
                        step_index=step_index,
                        node_id=node_id,
                        output_stream=self.output_stream,
                        context_files=request.context_files,
                        user_instruction=request.user_instruction,
                        agent_domain=self.manifest.get_agent_domain(agent_name),
                        llm_config=request.llm_config,
                        workflow_steps=workflow_steps,
                    )
                except Exception as step_err:
                    await self.output_stream.push(node_id, "error", {
                        "step_index": step_index,
                        "step_name": step_name,
                        "error": str(step_err),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    await self._log_audit(pid, node_id, AuditEventType.EXECUTION_ERROR,
                        step_index=step_index, step_name=step_name,
                        data={"error": str(step_err)},
                        actor=f"agent:{agent_name}")
                    self.node_state.transition(node_id, NodeStatus.FAILED)
                    await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                        data={"previous": "running", "new": "failed"})
                    await self.output_stream.push(node_id, "done", {
                        "status": "failed",
                        "error": str(step_err),
                    })
                    await self.output_stream.set_active(node_id, False)
                    await self.checkpoint_mgr.cleanup(node_id)
                    return

                # Record step result
                await self.checkpoint_mgr.record_step_result(node_id, step_index, step_result)

                # Audit: step output + persist to node.output_log
                await self._log_audit(pid, node_id, AuditEventType.STEP_OUTPUT,
                    step_index=step_index, step_name=step_name,
                    data={"summary": step_result.get("summary", ""),
                          "output_preview": str(step_result.get("output", ""))[:500]},
                    actor=f"agent:{agent_name}")
                await self._populate_output_log(pid, node_id, step_index, step_name, step_result)

                # Audit: step end
                await self._log_audit(pid, node_id, AuditEventType.STEP_END,
                    step_index=step_index, step_name=step_name,
                    data={"result_summary": step_result.get("summary", "Step completed")},
                    actor=f"agent:{agent_name}")

                # Announce step end
                await self.output_stream.push(node_id, "step_end", {
                    "step_index": step_index,
                    "step_name": step_name,
                    "result_summary": step_result.get("summary", "Step completed"),
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # Check if we should pause at checkpoint
                if await self.checkpoint_mgr.should_pause(node_id, step_config):
                    await self.checkpoint_mgr.pause(
                        node_id,
                        reason=f"Checkpoint: {step_name}",
                        confirmation_data=step_result,
                    )
                    self.node_state.transition(node_id, NodeStatus.PAUSED)

                    safety = step_config.get("safety_impact", "low")

                    # Audit: checkpoint reached
                    await self._log_audit(pid, node_id, AuditEventType.CHECKPOINT_REACHED,
                        step_index=step_index, step_name=step_name,
                        data={"safety_impact": safety,
                              "output_preview": step_result.get("summary", "")})

                    await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                        data={"previous": "running", "new": "paused"})

                    await self.output_stream.push(node_id, "checkpoint", {
                        "step_index": step_index,
                        "step_name": step_name,
                        "message": f"Execution paused at '{step_name}'. Review output and continue or chat.",
                        "output_preview": step_result.get("summary", ""),
                        "safety_impact": safety,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                    # Determine timeout based on safety level
                    safety = step_config.get("safety_impact", "low")
                    timeout = 0 if safety in ("high", "critical") else 1800  # 30min for low/medium

                    # Wait for resume signal
                    wait_count = 0
                    while await self.checkpoint_mgr.is_paused(node_id):
                        await asyncio.sleep(1)
                        wait_count += 1
                        # Check approval status for audit
                        approval_status = await self.checkpoint_mgr.get_approval_status(node_id)
                        if approval_status == "approved":
                            await self._log_audit(pid, node_id, AuditEventType.CHECKPOINT_APPROVED,
                                step_index=step_index, step_name=step_name,
                                data={"decided_by": "user", "reason": ""},
                                actor="user")
                            break
                        elif approval_status == "rejected":
                            await self._log_audit(pid, node_id, AuditEventType.CHECKPOINT_REJECTED,
                                step_index=step_index, step_name=step_name,
                                data={"decided_by": "user", "reason": ""},
                                actor="user")
                            break

                        # Timeout check (skip for high/critical)
                        if timeout > 0 and wait_count > timeout:
                            await self.output_stream.push(node_id, "error", {
                                "error": f"Checkpoint wait timeout ({timeout}s). Execution cancelled.",
                            })
                            self.node_state.transition(node_id, NodeStatus.CANCELLED)
                            await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                                data={"previous": "paused", "new": "cancelled"})
                            await self.output_stream.set_active(node_id, False)
                            await self.checkpoint_mgr.cleanup(node_id)
                            return

                        # Recheck for cancellation
                        if self.node_state.get_status(node_id) == NodeStatus.CANCELLED:
                            await self.output_stream.set_active(node_id, False)
                            await self.checkpoint_mgr.cleanup(node_id)
                            return

                    # If rejected, stop the agent
                    if await self.checkpoint_mgr.get_approval_status(node_id) == "rejected":
                        self.node_state.transition(node_id, NodeStatus.CANCELLED)
                        await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                            data={"previous": "paused", "new": "cancelled"})
                        await self.output_stream.push(node_id, "error", {
                            "error": "Checkpoint rejected by user. Execution cancelled.",
                        })
                        await self.output_stream.set_active(node_id, False)
                        await self.checkpoint_mgr.cleanup(node_id)
                        return

                    self.node_state.transition(node_id, NodeStatus.RUNNING)
                    await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                        data={"previous": "paused", "new": "running"})
                    await self.output_stream.push(node_id, "output", {
                        "text": f"Resuming execution after '{step_name}'...",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            # Check final status
            final_status = self.node_state.get_status(node_id)
            if final_status == NodeStatus.RUNNING:
                self.node_state.transition(node_id, NodeStatus.COMPLETED)
                await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                    data={"previous": "running", "new": "completed"})

            # Deliverables from workflow
            deliverables = []
            for i, step in enumerate(workflow_steps):
                deliverables.append(step.get("deliverable", f"step_{i+1}_output.md"))

            # Audit: execution complete
            await self._log_audit(pid, node_id, AuditEventType.EXECUTION_COMPLETE,
                data={"status": self.node_state.get_status(node_id).value,
                      "deliverables": deliverables,
                      "total_steps": total_steps},
                actor=f"agent:{agent_name}")

            await self.output_stream.push(node_id, "done", {
                "status": self.node_state.get_status(node_id).value,
                "deliverables": deliverables,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Update node completed_at
            self.node_state.set_completed_at(node_id, datetime.utcnow().isoformat())

        except asyncio.CancelledError:
            self.node_state.transition(node_id, NodeStatus.CANCELLED)
            await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                data={"previous": "running", "new": "cancelled"})
            await self.output_stream.push(node_id, "done", {
                "status": "cancelled",
            })
        except Exception as e:
            self.node_state.transition(node_id, NodeStatus.FAILED)
            await self._log_audit(pid, node_id, AuditEventType.EXECUTION_ERROR,
                data={"error": str(e), "traceback": traceback.format_exc()[-500:]})
            await self._log_audit(pid, node_id, AuditEventType.NODE_STATUS_CHANGE,
                data={"previous": "running", "new": "failed"})
            await self.output_stream.push(node_id, "error", {
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            await self.output_stream.push(node_id, "done", {
                "status": "failed",
                "error": str(e),
            })
        finally:
            await self.output_stream.set_active(node_id, False)
            await self.checkpoint_mgr.cleanup(node_id)
            async with self._task_lock:
                self._active_tasks.pop(node_id, None)

    async def stop_agent(self, node_id: str) -> bool:
        """
        Stop a running agent by cancelling its task.
        Returns True if a task was found and cancelled.
        """
        async with self._task_lock:
            task = self._active_tasks.get(node_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self.node_state.transition(node_id, NodeStatus.CANCELLED)
            await self.output_stream.push(node_id, "output", {
                "text": "Agent execution stopped by user.",
                "timestamp": datetime.utcnow().isoformat(),
            })
            await self.output_stream.push(node_id, "done", {
                "status": "cancelled",
            })
            return True
        return False

    async def continue_from_checkpoint(self, node_id: str) -> bool:
        """Resume execution from a checkpoint pause. Returns True if was paused."""
        return await self.checkpoint_mgr.resume(node_id)

    async def chat_at_checkpoint(self, node_id: str, message: str) -> Dict[str, Any]:
        """
        Send a chat message to the agent at a checkpoint.
        Returns the agent's chat response.
        """
        await self.checkpoint_mgr.add_chat_message(node_id, "user", message)

        # Generate a response based on the current step context
        state = self.checkpoint_mgr.get_state_snapshot(node_id)
        current_step = state.get("current_step", 0)

        response_text = (
            f"Received your message at step {current_step}: \"{message}\"\n\n"
            f"I'll incorporate this into the next steps. You can continue execution "
            f"or ask further questions."
        )

        await self.checkpoint_mgr.add_chat_message(node_id, "agent", response_text)

        await self.output_stream.push(node_id, "output", {
            "text": f"[Chat] User: {message}",
            "timestamp": datetime.utcnow().isoformat(),
        })
        await self.output_stream.push(node_id, "output", {
            "text": f"[Chat] Agent: {response_text}",
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "role": "agent",
            "content": response_text,
            "chat_history": await self.checkpoint_mgr.get_chat_history(node_id),
        }

    def is_running(self, node_id: str) -> bool:
        """Check if a node is currently executing."""
        task = self._active_tasks.get(node_id)
        return task is not None and not task.done()

    def get_running_nodes(self) -> List[str]:
        """Get list of currently running node IDs."""
        return [
            nid for nid, task in self._active_tasks.items()
            if not task.done()
        ]
