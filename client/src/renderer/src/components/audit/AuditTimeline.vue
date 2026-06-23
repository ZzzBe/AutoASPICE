<template>
  <div class="audit-timeline">
    <div v-if="events.length === 0" class="timeline-empty">
      <el-icon :size="36"><Document /></el-icon>
      <p>No audit events found.</p>
    </div>

    <el-timeline v-else>
      <el-timeline-item
        v-for="event in events"
        :key="event.event_id"
        :timestamp="formatTimestamp(event.timestamp)"
        :type="eventTypeColor(event.event_type)"
        :hollow="false"
        placement="top"
      >
        <div class="timeline-event" @click="toggleExpand(event.event_id)">
          <div class="event-header">
            <el-tag :type="eventTypeTag(event.event_type)" size="small" class="event-type-badge">
              {{ formatEventType(event.event_type) }}
            </el-tag>
            <span v-if="event.step_name" class="event-step">{{ event.step_name }}</span>
            <span class="event-node">{{ event.node_id }}</span>
            <span class="event-actor">{{ event.actor }}</span>
          </div>

          <div v-if="expandedEvents.has(event.event_id)" class="event-detail">
            <div class="event-data">
              <div v-for="(value, key) in event.data" :key="key" class="data-row">
                <span class="data-key">{{ key }}:</span>
                <span class="data-value">{{ truncateValue(value) }}</span>
              </div>
            </div>

            <!-- For step_output events, show a link to view full output -->
            <div v-if="event.event_type === 'step_output' && event.data?.output_preview" class="event-output-preview">
              <div class="output-preview-header">
                <el-icon><View /></el-icon>
                <span>Output Preview</span>
              </div>
              <pre class="output-preview-content">{{ event.data.output_preview }}</pre>
            </div>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  events: { type: Array, default: () => [] },
})

const expandedEvents = ref(new Set())

function toggleExpand(eventId) {
  if (expandedEvents.value.has(eventId)) {
    expandedEvents.value.delete(eventId)
  } else {
    expandedEvents.value.add(eventId)
  }
  expandedEvents.value = new Set(expandedEvents.value)
}

function formatTimestamp(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
}

function formatEventType(type) {
  const labels = {
    node_created: 'Node Created',
    node_status_change: 'Status Change',
    step_start: 'Step Start',
    step_end: 'Step End',
    step_output: 'Step Output',
    checkpoint_reached: 'Checkpoint',
    checkpoint_chat: 'Chat',
    checkpoint_approved: 'Approved',
    checkpoint_rejected: 'Rejected',
    execution_complete: 'Complete',
    execution_error: 'Error',
  }
  return labels[type] || type
}

function eventTypeColor(type) {
  const map = {
    node_created: '#6366f1',
    node_status_change: '#8b5cf6',
    step_start: '#3b82f6',
    step_end: '#10b981',
    step_output: '#06b6d4',
    checkpoint_reached: '#f59e0b',
    checkpoint_chat: '#a855f7',
    checkpoint_approved: '#22c55e',
    checkpoint_rejected: '#ef4444',
    execution_complete: '#22c55e',
    execution_error: '#ef4444',
  }
  return map[type] || '#6b7280'
}

function eventTypeTag(type) {
  const map = {
    node_created: '',
    node_status_change: 'info',
    step_start: '',
    step_end: 'success',
    step_output: '',
    checkpoint_reached: 'warning',
    checkpoint_chat: '',
    checkpoint_approved: 'success',
    checkpoint_rejected: 'danger',
    execution_complete: 'success',
    execution_error: 'danger',
  }
  return map[type] || 'info'
}

function truncateValue(value) {
  if (typeof value === 'string') {
    return value.length > 200 ? value.slice(0, 200) + '...' : value
  }
  if (typeof value === 'object') {
    const str = JSON.stringify(value, null, 0)
    return str.length > 200 ? str.slice(0, 200) + '...' : str
  }
  return String(value)
}
</script>

<style scoped>
.audit-timeline {
  padding: 0 8px;
}

.timeline-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  color: var(--color-text-muted);
  gap: 12px;
}

.timeline-event {
  cursor: pointer;
  padding: 4px 0;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.event-type-badge {
  flex-shrink: 0;
}

.event-step {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.event-node {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.event-actor {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-left: auto;
}

.event-detail {
  margin-top: 10px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.event-data {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.data-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.data-key {
  color: var(--color-text-muted);
  min-width: 100px;
  font-weight: 500;
}

.data-value {
  color: var(--color-text-primary);
  word-break: break-all;
}

.event-output-preview {
  margin-top: 8px;
}

.output-preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 6px;
}

.output-preview-content {
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.5;
  color: var(--color-text-primary);
  background: var(--color-bg-code);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}
</style>
