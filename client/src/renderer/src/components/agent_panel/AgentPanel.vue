<template>
  <div class="agent-panel">
    <!-- No node selected -->
    <div v-if="!node" class="panel-empty">
      <el-icon :size="48"><MagicStick /></el-icon>
      <h3>Select a Node</h3>
      <p>Choose a node from the project tree to view or execute an agent.</p>
    </div>

    <template v-else>
      <!-- Panel Header -->
      <div class="panel-header">
        <div class="panel-header-info">
          <span class="panel-node-name">{{ node.name }}</span>
          <el-tag
            :type="statusTagType"
            size="small"
          >{{ statusLabel }}</el-tag>
        </div>
        <div class="panel-header-actions">
          <el-button
            v-if="!execState || execState.status === 'stopped' || execState.status === 'failed'"
            type="primary"
            size="small"
            @click="showContextSelector = true"
          >
            <el-icon><VideoPlay /></el-icon>
            Start Agent
          </el-button>
          <el-button
            v-if="execState?.status === 'running'"
            type="danger"
            size="small"
            @click="handleStop"
          >
            <el-icon><VideoPause /></el-icon>
            Stop
          </el-button>
        </div>
      </div>

      <!-- State: Not Started -->
      <div v-if="!execState || execState.status === 'stopped'" class="panel-state">
        <div class="state-not-started">
          <el-icon :size="32"><CirclePlus /></el-icon>
          <p>Agent not yet started</p>
          <el-button type="primary" @click="showContextSelector = true">
            Start with Context
          </el-button>
        </div>
      </div>

      <!-- State: Running -->
      <div v-else-if="execState.status === 'running'" class="panel-state panel-state--running">
        <WorkflowSteps :steps="workflowSteps" />
        <div class="output-section">
          <OutputStream
            :lines="outputLines"
            @clear="handleClearOutput"
          />
        </div>
      </div>

      <!-- State: Checkpoint -->
      <div v-else-if="execState.status === 'checkpoint'" class="panel-state">
        <div class="output-section">
          <OutputStream
            :lines="outputLines"
            @clear="handleClearOutput"
          />
        </div>
        <ChatPanel
          :node-id="node.id"
          :checkpoint-id="execState.checkpointId"
          :step-output="currentStepOutput"
          :safety-impact="currentSafetyImpact"
          :approval-status="currentApprovalStatus"
          @continue="handleContinue"
          @approve="handleApprove"
          @reject="handleReject"
        />
      </div>

      <!-- State: Completed -->
      <div v-else-if="execState.status === 'completed'" class="panel-state">
        <div class="state-completed">
          <el-icon :size="36" color="var(--color-success)"><CircleCheck /></el-icon>
          <h4>Execution Completed</h4>
          <p>All workflow steps finished successfully.</p>
        </div>
        <div class="output-section">
          <OutputStream
            :lines="outputLines"
            @clear="handleClearOutput"
          />
        </div>
      </div>

      <!-- State: Failed -->
      <div v-else-if="execState.status === 'failed'" class="panel-state">
        <div class="state-failed">
          <el-icon :size="36" color="var(--color-error)"><CircleClose /></el-icon>
          <h4>Execution Failed</h4>
          <p>{{ execState.error || 'An unknown error occurred.' }}</p>
          <el-button type="primary" @click="handleRetry">
            <el-icon><Refresh /></el-icon>
            Retry
          </el-button>
        </div>
        <div class="output-section">
          <OutputStream
            :lines="outputLines"
            @clear="handleClearOutput"
          />
        </div>
      </div>
    </template>

    <!-- Context Selector Dialog -->
    <ContextSelector
      v-if="showContextSelector"
      :node="node"
      :project-id="projectId"
      @confirm="handleStartAgent"
      @cancel="showContextSelector = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../../store/project'
import { useAgentStore } from '../../store/agent'
import WorkflowSteps from './WorkflowSteps.vue'
import OutputStream from './OutputStream.vue'
import ChatPanel from '../chat/ChatPanel.vue'
import ContextSelector from '../context_selector/ContextSelector.vue'

const props = defineProps({
  projectId: { type: String, required: true }
})

const projectStore = useProjectStore()
const agentStore = useAgentStore()

const node = computed(() => projectStore.selectedNodeData)
const execState = computed(() => {
  const id = projectStore.selectedNode
  return id ? agentStore.getNodeExecutionState(id) : null
})
const outputLines = computed(() => {
  const id = projectStore.selectedNode
  return id ? agentStore.getNodeOutput(id) : []
})
const workflowSteps = computed(() => {
  const state = execState.value
  return state?.steps || []
})

const showContextSelector = ref(false)

// Computed properties for checkpoint/approval context
const currentStepOutput = computed(() => {
  const checkpoints = agentStore.getNodeCheckpoints(projectStore.selectedNode)
  const last = checkpoints[checkpoints.length - 1]
  return last?.output_preview || last?.step_result || null
})

const currentSafetyImpact = computed(() => {
  const checkpoints = agentStore.getNodeCheckpoints(projectStore.selectedNode)
  const last = checkpoints[checkpoints.length - 1]
  return last?.safety_impact || 'low'
})

const currentApprovalStatus = computed(() => {
  const checkpoints = agentStore.getNodeCheckpoints(projectStore.selectedNode)
  const last = checkpoints[checkpoints.length - 1]
  if (!last) return null
  // Check if this is a high/critical step that requires approval
  const safety = last?.safety_impact || 'low'
  return (safety === 'high' || safety === 'critical') ? 'pending' : null
})

const statusTagType = computed(() => {
  const s = execState.value?.status || node.value?.status || 'idle'
  const map = {
    running: 'primary',
    checkpoint: 'warning',
    completed: 'success',
    failed: 'danger',
    stopped: 'info',
    idle: 'info',
    pending: 'info'
  }
  return map[s] || 'info'
})

const statusLabel = computed(() => {
  const s = execState.value?.status || node.value?.status || 'idle'
  const map = {
    running: 'Running',
    checkpoint: 'Checkpoint',
    completed: 'Completed',
    failed: 'Failed',
    stopped: 'Stopped',
    idle: 'Idle',
    pending: 'Pending'
  }
  return map[s] || s
})

async function handleStartAgent(context) {
  showContextSelector.value = false
  const nodeId = projectStore.selectedNode
  if (!nodeId) return

  try {
    await agentStore.executeAgent(props.projectId, nodeId, {
      context: context?.files || [],
      params: context?.params || {}
    })
    ElMessage.success('Agent started')
  } catch (err) {
    ElMessage.error(err.message || 'Failed to start agent')
  }
}

async function handleStop() {
  const state = execState.value
  if (!state) return
  try {
    await agentStore.stopAgent(state.agent_id || projectStore.selectedNode)
    ElMessage.success('Agent stopped')
  } catch (err) {
    ElMessage.error('Failed to stop agent')
  }
}

async function handleContinue(checkpointId) {
  const state = execState.value
  if (!state) return
  try {
    await agentStore.continueFromCheckpoint(
      state.agent_id || projectStore.selectedNode,
      checkpointId
    )
    ElMessage.success('Continuing from checkpoint')
  } catch (err) {
    ElMessage.error('Failed to continue')
  }
}

async function handleApprove(checkpointId, reason) {
  const nodeId = projectStore.selectedNode
  if (!nodeId) return
  try {
    await agentStore.approveCheckpoint(nodeId, reason)
    ElMessage.success('Checkpoint approved — resuming execution')
  } catch (err) {
    ElMessage.error(err.message || 'Failed to approve')
  }
}

async function handleReject(checkpointId, reason) {
  const nodeId = projectStore.selectedNode
  if (!nodeId) return
  try {
    await agentStore.rejectCheckpoint(nodeId, reason)
    ElMessage.success('Checkpoint rejected — agent stopped')
  } catch (err) {
    ElMessage.error(err.message || 'Failed to reject')
  }
}

async function handleRetry() {
  showContextSelector.value = true
}

function handleClearOutput() {
  const nodeId = projectStore.selectedNode
  if (nodeId) {
    agentStore.clearNodeState(nodeId)
  }
}
</script>

<style scoped>
.agent-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-primary);
}

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--color-text-muted);
}

.panel-empty h3 {
  color: var(--color-text-secondary);
  font-size: 16px;
  font-weight: 600;
}

.panel-empty p {
  font-size: 13px;
  max-width: 300px;
  text-align: center;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.panel-header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-node-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.panel-header-actions {
  display: flex;
  gap: 8px;
}

.panel-state {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.panel-state--running {
  /* special running layout */
}

.state-not-started,
.state-completed,
.state-failed {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  gap: 8px;
  text-align: center;
}

.state-not-started p,
.state-completed p,
.state-failed p {
  color: var(--color-text-secondary);
  font-size: 13px;
  max-width: 320px;
}

.state-not-started h4,
.state-completed h4,
.state-failed h4 {
  color: var(--color-text-primary);
  font-size: 15px;
}

.output-section {
  flex: 1;
  min-height: 200px;
  padding: 0 8px 8px;
  overflow: hidden;
}
</style>
