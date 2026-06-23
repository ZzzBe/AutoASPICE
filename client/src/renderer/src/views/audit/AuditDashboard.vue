<template>
  <div class="audit-dashboard">
    <!-- Header -->
    <div class="audit-header">
      <div class="audit-header-left">
        <el-button size="small" text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          Back
        </el-button>
        <h2 class="audit-title">Audit Trail</h2>
        <el-tag size="small" type="info">{{ projectId }}</el-tag>
      </div>
      <div class="audit-header-right">
        <el-button size="small" :loading="loading" @click="refresh">
          <el-icon><Refresh /></el-icon>
          Refresh
        </el-button>
      </div>
    </div>

    <!-- Summary stats -->
    <div v-if="summary" class="summary-cards">
      <div class="summary-card">
        <div class="summary-value">{{ summary.total_events }}</div>
        <div class="summary-label">Total Events</div>
      </div>
      <div class="summary-card">
        <div class="summary-value text-success">{{ summary.approvals }}</div>
        <div class="summary-label">Approvals</div>
      </div>
      <div class="summary-card">
        <div class="summary-value text-danger">{{ summary.rejections }}</div>
        <div class="summary-label">Rejections</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ Object.keys(summary.node_summaries || {}).length }}</div>
        <div class="summary-label">Nodes Tracked</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-select
        v-model="auditStore.filters.nodeId"
        placeholder="All Nodes"
        size="small"
        clearable
        style="width: 200px"
      >
        <el-option
          v-for="opt in auditStore.nodeOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>

      <el-select
        v-model="auditStore.filters.eventTypes"
        placeholder="All Event Types"
        size="small"
        multiple
        clearable
        collapse-tags
        collapse-tags-tooltip
        style="width: 260px"
      >
        <el-option label="Node Created" value="node_created" />
        <el-option label="Status Change" value="node_status_change" />
        <el-option label="Step Start" value="step_start" />
        <el-option label="Step End" value="step_end" />
        <el-option label="Step Output" value="step_output" />
        <el-option label="Checkpoint" value="checkpoint_reached" />
        <el-option label="Chat" value="checkpoint_chat" />
        <el-option label="Approved" value="checkpoint_approved" />
        <el-option label="Rejected" value="checkpoint_rejected" />
        <el-option label="Complete" value="execution_complete" />
        <el-option label="Error" value="execution_error" />
      </el-select>

      <el-button size="small" @click="auditStore.resetFilters()">Clear Filters</el-button>
      <span class="filter-count">{{ auditStore.filteredEvents.length }} events</span>
    </div>

    <!-- Timeline -->
    <div class="timeline-container" v-loading="loading">
      <AuditTimeline :events="auditStore.filteredEvents" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuditStore } from '../../store/audit'
import AuditTimeline from '../../components/audit/AuditTimeline.vue'

const route = useRoute()
const auditStore = useAuditStore()

const projectId = computed(() => route.params.projectId)
const loading = ref(false)
const summary = computed(() => auditStore.summary)

onMounted(async () => {
  await refresh()
})

async function refresh() {
  loading.value = true
  try {
    await Promise.all([
      auditStore.loadAuditTrail(projectId.value, { limit: 500 }),
      auditStore.loadSummary(projectId.value),
    ])
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.audit-dashboard {
  height: 100%;
  overflow-y: auto;
  padding: 20px 28px;
  display: flex;
  flex-direction: column;
}

.audit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.audit-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.audit-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.summary-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: center;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-accent);
  font-family: var(--font-mono);
}

.summary-value.text-success { color: var(--color-success); }
.summary-value.text-danger { color: var(--color-error); }

.summary-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  flex-shrink: 0;
}

.filter-count {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-text-muted);
}

.timeline-container {
  flex: 1;
  overflow-y: auto;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
}
</style>
