<template>
  <div class="output-stream" ref="containerRef">
    <div class="output-stream-header">
      <span class="output-title">Output</span>
      <div class="output-actions">
        <el-button size="small" text @click="clearOutput">
          <el-icon><Delete /></el-icon>
          Clear
        </el-button>
        <el-button size="small" text @click="copyOutput">
          <el-icon><CopyDocument /></el-icon>
          Copy
        </el-button>
      </div>
    </div>
    <div class="output-stream-content" ref="contentRef">
      <div v-if="lines.length === 0" class="output-empty">
        <el-icon :size="24"><Document /></el-icon>
        <p>Waiting for output...</p>
      </div>
      <div
        v-for="(line, index) in lines"
        :key="index"
        class="output-line"
        :class="lineClass(line)"
      >
        <span class="line-number">{{ index + 1 }}</span>
        <span class="line-text" v-html="formatLine(line)"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  lines: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['clear'])

const containerRef = ref(null)
const contentRef = ref(null)

function lineClass(line) {
  const text = typeof line === 'string' ? line : line.text || ''
  const lower = text.toLowerCase()
  if (lower.includes('error') || lower.includes('fail') || lower.includes('exception')) {
    return 'output-line--error'
  }
  if (lower.includes('warning') || lower.includes('warn')) {
    return 'output-line--warning'
  }
  if (lower.includes('success') || lower.includes('complete')) {
    return 'output-line--success'
  }
  if (lower.includes('checkpoint')) {
    return 'output-line--checkpoint'
  }
  return ''
}

function formatLine(line) {
  const text = typeof line === 'string' ? line : line.text || ''
  // Escape HTML
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Simple ANSI-like formatting
  return escaped
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
}

function clearOutput() {
  emit('clear')
}

async function copyOutput() {
  const text = props.lines
    .map((l) => (typeof l === 'string' ? l : l.text || ''))
    .join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('Output copied to clipboard')
  } catch {
    ElMessage.error('Failed to copy')
  }
}

// Auto-scroll to bottom on new lines
watch(
  () => props.lines.length,
  async () => {
    await nextTick()
    if (contentRef.value) {
      contentRef.value.scrollTop = contentRef.value.scrollHeight
    }
  }
)
</script>

<style scoped>
.output-stream {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0a0e14;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.output-stream-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.output-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.output-actions {
  display: flex;
  gap: 4px;
}

.output-stream-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
}

.output-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: var(--color-text-muted);
}

.output-line {
  display: flex;
  padding: 0 12px;
  transition: background var(--transition-fast);
}

.output-line:hover {
  background: rgba(255, 255, 255, 0.02);
}

.line-number {
  display: inline-block;
  width: 40px;
  text-align: right;
  padding-right: 12px;
  color: var(--color-text-muted);
  opacity: 0.5;
  flex-shrink: 0;
  user-select: none;
}

.line-text {
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}

.output-line--error .line-text {
  color: var(--color-error);
}

.output-line--warning .line-text {
  color: var(--color-warning);
}

.output-line--success .line-text {
  color: var(--color-success);
}

.output-line--checkpoint .line-text {
  color: var(--color-accent);
}

.output-line--checkpoint {
  background: rgba(88, 166, 255, 0.05);
}

.inline-code {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 11px;
}
</style>
