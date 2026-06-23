import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

export const useAuditStore = defineStore('audit', () => {
  // ── State ───────────────────────────────────────────────────
  const events = ref([])
  const loading = ref(false)
  const summary = ref(null)
  const filters = reactive({
    nodeId: null,
    eventTypes: [],
    timeFrom: null,
    timeTo: null,
  })

  // ── Getters ─────────────────────────────────────────────────
  const filteredEvents = computed(() => {
    let result = [...events.value]

    if (filters.nodeId) {
      result = result.filter(e => e.node_id === filters.nodeId)
    }
    if (filters.eventTypes && filters.eventTypes.length > 0) {
      result = result.filter(e => filters.eventTypes.includes(e.event_type))
    }
    if (filters.timeFrom) {
      result = result.filter(e => e.timestamp >= filters.timeFrom)
    }
    if (filters.timeTo) {
      result = result.filter(e => e.timestamp <= filters.timeTo)
    }

    return result
  })

  const eventCounts = computed(() => {
    const counts = {}
    for (const e of filteredEvents.value) {
      const type = e.event_type || 'unknown'
      counts[type] = (counts[type] || 0) + 1
    }
    return counts
  })

  const nodeOptions = computed(() => {
    const nodeIds = new Set()
    for (const e of events.value) {
      if (e.node_id) nodeIds.add(e.node_id)
    }
    return Array.from(nodeIds).map(id => ({ value: id, label: id }))
  })

  // ── Actions ─────────────────────────────────────────────────

  async function loadAuditTrail(projectId, queryParams = {}) {
    loading.value = true
    try {
      const result = await window.autodev.getAuditTrail({
        projectId,
        ...queryParams,
      })
      if (result.success) {
        events.value = result.data?.events || []
      }
    } catch (err) {
      console.error('Failed to load audit trail:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadNodeAudit(projectId, nodeId) {
    loading.value = true
    try {
      const result = await window.autodev.getNodeAudit({ projectId, nodeId })
      if (result.success) {
        events.value = result.data?.events || []
      }
    } catch (err) {
      console.error('Failed to load node audit:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadSummary(projectId) {
    try {
      const result = await window.autodev.getAuditSummary(projectId)
      if (result.success) {
        summary.value = result.data
      }
    } catch (err) {
      console.error('Failed to load audit summary:', err)
    }
  }

  function setFilters(newFilters) {
    Object.assign(filters, newFilters)
  }

  function resetFilters() {
    filters.nodeId = null
    filters.eventTypes = []
    filters.timeFrom = null
    filters.timeTo = null
  }

  return {
    // State
    events,
    loading,
    summary,
    filters,
    // Getters
    filteredEvents,
    eventCounts,
    nodeOptions,
    // Actions
    loadAuditTrail,
    loadNodeAudit,
    loadSummary,
    setFilters,
    resetFilters,
  }
})
