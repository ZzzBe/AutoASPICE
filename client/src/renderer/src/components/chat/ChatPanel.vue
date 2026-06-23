<template>
  <div class="chat-panel">
    <!-- Safety Impact Banner (high/critical only) -->
    <div v-if="safetyImpact === 'critical' || safetyImpact === 'high'" class="safety-banner" :class="`safety-banner--${safetyImpact}`">
      <el-icon :size="18"><WarningFilled /></el-icon>
      <span class="safety-banner-text">
        <strong>Human Approval Required</strong> — This step has <code>{{ safetyImpact }}</code> safety impact. Review the output before approving.
      </span>
    </div>

    <!-- Step Output Preview -->
    <div v-if="stepOutput && hasStepOutput" class="step-output-preview">
      <div class="step-output-header" @click="outputExpanded = !outputExpanded">
        <div class="step-output-title">
          <el-icon><Document /></el-icon>
          <span>Step Output Preview</span>
        </div>
        <div class="step-output-toggle">
          <el-tag :type="safetyTagType" size="small">{{ safetyLabel }}</el-tag>
          <el-icon :class="{ rotated: outputExpanded }"><ArrowDown /></el-icon>
        </div>
      </div>
      <div v-if="outputExpanded" class="step-output-body">
        <div class="step-output-summary">{{ stepOutput.summary || stepOutput.output || 'No summary available.' }}</div>
        <div v-if="stepOutput.output_lines && stepOutput.output_lines.length" class="step-output-lines">
          <div v-for="(line, i) in stepOutput.output_lines.slice(0, 20)" :key="i" class="output-line">
            <span class="output-line-num">{{ i + 1 }}</span>
            <span class="output-line-text">{{ line }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Header -->
    <div class="chat-header">
      <div class="chat-header-title">
        <el-icon><ChatDotRound /></el-icon>
        <span>Checkpoint Discussion</span>
      </div>
      <el-tag v-if="approvalStatus === 'pending'" size="small" type="warning">Awaiting Approval</el-tag>
      <el-tag v-else size="small" type="warning">Checkpoint</el-tag>
    </div>

    <!-- Messages -->
    <div class="chat-messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="chat-empty">
        <p>Ask questions about the current state or request changes before continuing.</p>
      </div>
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="chat-message"
        :class="{ 'chat-message--user': msg.role === 'user', 'chat-message--agent': msg.role === 'assistant' }"
      >
        <div class="message-bubble">
          <div class="message-role">{{ msg.role === 'user' ? 'You' : 'Agent' }}</div>
          <div class="message-content" v-html="formatMessage(msg.content)"></div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="sending" class="chat-message chat-message--agent">
        <div class="message-bubble">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input-area">
      <!-- Approval reason input (shown when approve/reject buttons visible) -->
      <div v-if="approvalStatus === 'pending'" class="approval-reason-row">
        <el-input
          v-model="approvalReason"
          placeholder="Enter reason for your decision (optional)..."
          size="small"
          :disabled="sending"
        />
      </div>

      <div class="chat-input-row">
        <el-input
          v-model="inputText"
          placeholder="Ask a question or provide feedback..."
          :disabled="sending"
          @keydown.enter="handleSend"
          size="small"
        >
          <template #suffix>
            <el-button
              :icon="Promotion"
              :disabled="!inputText.trim() || sending"
              :loading="sending"
              @click="handleSend"
              size="small"
              text
            />
          </template>
        </el-input>
      </div>

      <div class="chat-actions">
        <!-- Approve/Reject buttons (shown for high/critical checkpoints) -->
        <template v-if="approvalStatus === 'pending'">
          <el-button
            size="small"
            type="success"
            @click="handleApprove"
          >
            <el-icon><CircleCheck /></el-icon>
            Approve
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click="handleReject"
          >
            <el-icon><CircleClose /></el-icon>
            Reject
          </el-button>
        </template>
        <!-- Continue button (shown for low/medium checkpoints without approval requirement) -->
        <el-button
          v-else
          size="small"
          type="primary"
          @click="$emit('continue', checkpointId)"
        >
          <el-icon><VideoPlay /></el-icon>
          Continue Execution
        </el-button>
      </div>
    </div>

    <!-- Reject confirmation dialog -->
    <el-dialog v-model="showRejectConfirm" title="Reject This Step?" width="420px" append-to-body>
      <p style="margin-bottom: 16px; color: var(--color-text-secondary); font-size: 13px;">
        Rejecting will stop the agent execution. The agent's output will be discarded.
      </p>
      <el-input
        v-model="approvalReason"
        placeholder="Enter rejection reason..."
        type="textarea"
        :rows="3"
      />
      <template #footer>
        <el-button @click="showRejectConfirm = false">Cancel</el-button>
        <el-button type="danger" @click="confirmReject">Yes, Reject</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import { useAgentStore } from '../../store/agent'

const props = defineProps({
  nodeId: { type: String, required: true },
  checkpointId: { type: String, default: null },
  stepOutput: { type: Object, default: null },
  safetyImpact: { type: String, default: 'low' },
  approvalStatus: { type: String, default: null },
})

const emit = defineEmits(['continue', 'approve', 'reject'])

const agentStore = useAgentStore()

const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const messagesRef = ref(null)
const outputExpanded = ref(true)
const approvalReason = ref('')
const showRejectConfirm = ref(false)

const hasStepOutput = computed(() => {
  if (!props.stepOutput) return false
  return !!(props.stepOutput.summary || props.stepOutput.output || props.stepOutput.output_lines?.length)
})

const safetyTagType = computed(() => {
  const map = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[props.safetyImpact] || 'info'
})

const safetyLabel = computed(() => {
  const map = { low: 'Low Impact', medium: 'Medium Impact', high: 'High Impact', critical: 'Critical Impact' }
  return map[props.safetyImpact] || props.safetyImpact
})

function formatMessage(content) {
  if (!content) return ''
  return String(content)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>')
    .replace(/\n/g, '<br>')
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  messages.value.push({
    role: 'user',
    content: text,
    timestamp: Date.now()
  })
  inputText.value = ''
  sending.value = true

  await scrollToBottom()

  try {
    const state = agentStore.getNodeExecutionState(props.nodeId)
    const agentId = state?.agent_id || props.nodeId

    const result = await agentStore.sendChatMessage(
      agentId,
      props.checkpointId,
      text
    )

    if (result) {
      messages.value.push({
        role: 'assistant',
        content: result.response || result.content || 'Received.',
        timestamp: Date.now()
      })
    }
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: `Error: ${err.message}`,
      timestamp: Date.now()
    })
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

function handleApprove() {
  emit('approve', props.checkpointId, approvalReason.value)
}

function handleReject() {
  showRejectConfirm.value = true
}

function confirmReject() {
  showRejectConfirm.value = false
  emit('reject', props.checkpointId, approvalReason.value)
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--color-border);
  max-height: 500px;
  min-height: 250px;
}

/* Safety banner */
.safety-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  font-size: 12px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border);
}
.safety-banner--high {
  background: rgba(218, 54, 51, 0.08);
  color: var(--color-error);
  border-bottom-color: rgba(218, 54, 51, 0.2);
}
.safety-banner--critical {
  background: rgba(218, 54, 51, 0.12);
  color: var(--color-error);
  border-bottom-color: rgba(218, 54, 51, 0.3);
  animation: pulse-border 2s infinite;
}
@keyframes pulse-border {
  0%, 100% { border-bottom-color: rgba(218, 54, 51, 0.3); }
  50% { border-bottom-color: rgba(218, 54, 51, 0.6); }
}
.safety-banner-text code {
  background: rgba(255, 255, 255, 0.1);
  padding: 0 4px;
  border-radius: 2px;
  font-weight: 700;
  text-transform: uppercase;
}

/* Step output preview */
.step-output-preview {
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.step-output-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  background: var(--color-bg-secondary);
  user-select: none;
}
.step-output-header:hover {
  background: var(--color-bg-hover);
}
.step-output-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.step-output-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
}
.step-output-toggle .el-icon {
  transition: transform 0.2s;
  color: var(--color-text-muted);
}
.step-output-toggle .el-icon.rotated {
  transform: rotate(180deg);
}
.step-output-body {
  padding: 12px 14px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-primary);
  max-height: 200px;
  overflow-y: auto;
}
.step-output-summary {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-bottom: 8px;
  padding: 8px 12px;
  background: rgba(88, 166, 255, 0.06);
  border-radius: var(--radius-sm);
}
.step-output-lines {
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.6;
  background: var(--color-bg-code);
  border-radius: var(--radius-sm);
  overflow-x: auto;
}
.output-line {
  display: flex;
  padding: 0 8px;
}
.output-line-num {
  color: var(--color-text-muted);
  min-width: 28px;
  text-align: right;
  margin-right: 12px;
  user-select: none;
}
.output-line-text {
  color: var(--color-text-primary);
}

/* Chat header */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(210, 153, 34, 0.06);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.chat-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 16px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 12px;
}

.chat-message {
  display: flex;
}

.chat-message--user {
  justify-content: flex-end;
}

.chat-message--agent {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  font-size: 13px;
  line-height: 1.5;
}

.chat-message--user .message-bubble {
  background: rgba(88, 166, 255, 0.15);
  border: 1px solid rgba(88, 166, 255, 0.25);
  border-bottom-right-radius: 2px;
  color: var(--color-text-primary);
}

.chat-message--agent .message-bubble {
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 2px;
  color: var(--color-text-primary);
}

.message-role {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
  color: var(--color-text-muted);
}

.message-content {
  word-break: break-word;
}

.message-time {
  font-size: 10px;
  color: var(--color-text-muted);
  margin-top: 4px;
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

.chat-input-area {
  padding: 8px 12px 12px;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

.approval-reason-row {
  margin-bottom: 8px;
}

.chat-input-row {
  margin-bottom: 8px;
}

.chat-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.chat-inline-code {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 0.9em;
}
</style>
