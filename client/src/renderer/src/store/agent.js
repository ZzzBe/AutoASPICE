import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useAgentStore = defineStore('agent', () => {
  // ── State ───────────────────────────────────────────────────
  const executingNodes = ref(new Map())
  const outputStreams = ref(new Map())
  const checkpoints = ref(new Map())
  const wsCleanup = ref(null)
  const availableAgents = ref([])
  const domainsDetail = ref([])
  const ecosystemGraph = ref(null)

  // ── Actions ─────────────────────────────────────────────────
  function _getLLMConfig() {
    try {
      const STORAGE_PREFIX = 'autodev:apikey'
      const MODEL_STORAGE_PREFIX = 'autodev:model'
      const DEFAULT_PROVIDER_KEY = 'autodev:defaultProvider'
      const DEFAULT_MODELS = {
        openai: 'gpt-4o', anthropic: 'claude-sonnet-4-6',
        deepseek: 'deepseek-chat', google: 'gemini-2.5-flash', custom: '',
      }
      const provKey = localStorage.getItem(DEFAULT_PROVIDER_KEY)
      if (!provKey) return null
      const apiKey = localStorage.getItem(`${STORAGE_PREFIX}:${provKey}`)
      if (!apiKey) return null
      const model = localStorage.getItem(`${MODEL_STORAGE_PREFIX}:${provKey}`) || DEFAULT_MODELS[provKey] || ''
      return { provider: provKey, api_key: apiKey, model, base_url: '' }
    } catch { return null }
  }

  async function executeAgent(projectId, nodeId, params) {
    try {
      const llmConfig = _getLLMConfig()
      const result = await window.autodev.executeAgent({
        project_id: projectId,
        node_id: nodeId,
        llm_config: llmConfig || { provider: 'openai', api_key: '', model: 'gpt-4o', base_url: '' },
        ...params
      })
      if (result.success) {
        // Mark node as running
        executingNodes.value.set(nodeId, {
          status: 'running',
          startTime: Date.now(),
          projectId,
          ...result.data
        })

        // Initialize output stream
        if (!outputStreams.value.has(nodeId)) {
          outputStreams.value.set(nodeId, [])
        }

        // Connect WebSocket via preload message -- the main process handles WS
        return result.data
      }
      throw new Error(result.error || 'Failed to execute agent')
    } catch (err) {
      executingNodes.value.set(nodeId, {
        status: 'failed',
        error: err.message
      })
      throw err
    }
  }

  async function stopAgent(agentId) {
    try {
      const result = await window.autodev.stopAgent(agentId)
      if (result.success) {
        // Find the node with this agentId and update
        for (const [nodeId, data] of executingNodes.value.entries()) {
          if (data.agent_id === agentId || data.id === agentId) {
            executingNodes.value.set(nodeId, {
              ...data,
              status: 'stopped'
            })
          }
        }
      }
      return result
    } catch (err) {
      console.error('Failed to stop agent:', err)
      throw err
    }
  }

  async function getAgentStatus(agentId) {
    try {
      const result = await window.autodev.getAgentStatus(agentId)
      return result.success ? result.data : null
    } catch (err) {
      console.error('Failed to get agent status:', err)
      return null
    }
  }

  async function continueFromCheckpoint(agentId, checkpointId) {
    try {
      const result = await window.autodev.checkpointContinue({
        agentId,
        checkpointId
      })
      return result.success ? result.data : null
    } catch (err) {
      console.error('Failed to continue from checkpoint:', err)
      throw err
    }
  }

  async function sendChatMessage(agentId, checkpointId, message) {
    try {
      const result = await window.autodev.checkpointChat({
        agentId,
        checkpointId,
        message
      })
      return result.success ? result.data : null
    } catch (err) {
      console.error('Failed to send chat message:', err)
      throw err
    }
  }

  async function approveCheckpoint(nodeId, reason) {
    try {
      const result = await window.autodev.approveCheckpoint({ nodeId, reason })
      if (result.success) {
        if (executingNodes.value.has(nodeId)) {
          const current = executingNodes.value.get(nodeId)
          executingNodes.value.set(nodeId, { ...current, status: 'running', checkpointId: null })
        }
      }
      return result
    } catch (err) {
      console.error('Failed to approve checkpoint:', err)
      throw err
    }
  }

  async function rejectCheckpoint(nodeId, reason) {
    try {
      const result = await window.autodev.rejectCheckpoint({ nodeId, reason })
      if (result.success) {
        if (executingNodes.value.has(nodeId)) {
          const current = executingNodes.value.get(nodeId)
          executingNodes.value.set(nodeId, { ...current, status: 'stopped' })
        }
      }
      return result
    } catch (err) {
      console.error('Failed to reject checkpoint:', err)
      throw err
    }
  }

  async function loadDomainsDetail() {
    try {
      const r = await fetch('http://localhost:5090/agent/domains-detail')
      const d = await r.json()
      domainsDetail.value = d.domains || []
    } catch {
      // Electron IPC fallback
      try {
        if (window.autodev?.getDomainDetail) {
          const r = await window.autodev.getDomainDetail()
          if (r?.success) domainsDetail.value = r.data?.domains || []
        }
      } catch {}
    }
  }

  async function loadAgents() {
    try {
      const result = await window.autodev.listAgents()
      if (result.success) {
        availableAgents.value = result.data?.agents || result.data || []
      }
    } catch (err) {
      console.error('Failed to load agents:', err)
    }
  }

  async function loadEcosystemGraph() {
    try {
      const result = await window.autodev.getEcosystemGraph()
      if (result.success) {
        ecosystemGraph.value = result.data?.graph || result.data || null
      }
    } catch (err) {
      console.error('Failed to load ecosystem graph:', err)
    }
  }

  function appendOutput(nodeId, text) {
    const stream = outputStreams.value.get(nodeId) || []
    stream.push({
      text,
      timestamp: Date.now()
    })
    outputStreams.value.set(nodeId, [...stream])
  }

  function handleWsMessage(message) {
    const { type, projectId, nodeId, data } = message

    if (type === 'output' && nodeId) {
      if (data?.text) {
        appendOutput(nodeId, data.text)
      }
      if (data?.type === 'checkpoint') {
        const nodeCheckpoints = checkpoints.value.get(nodeId) || []
        nodeCheckpoints.push(data)
        checkpoints.value.set(nodeId, nodeCheckpoints)

        // Update node status
        if (executingNodes.value.has(nodeId)) {
          const current = executingNodes.value.get(nodeId)
          executingNodes.value.set(nodeId, {
            ...current,
            status: 'checkpoint',
            checkpointId: data.checkpoint_id || data.id
          })
        }
      }
      if (data?.type === 'complete') {
        if (executingNodes.value.has(nodeId)) {
          const current = executingNodes.value.get(nodeId)
          executingNodes.value.set(nodeId, {
            ...current,
            status: 'completed'
          })
        }
      }
      if (data?.type === 'error') {
        if (executingNodes.value.has(nodeId)) {
          const current = executingNodes.value.get(nodeId)
          executingNodes.value.set(nodeId, {
            ...current,
            status: 'failed',
            error: data.error || data.text
          })
        }
      }
    } else if (type === 'error' && nodeId) {
      appendOutput(nodeId, `[ERROR] ${message.error}`)
    }
  }

  function setupWsListener() {
    if (wsCleanup.value) {
      wsCleanup.value()
    }
    wsCleanup.value = window.autodev.onWsMessage(handleWsMessage)
  }

  function teardownWsListener() {
    if (wsCleanup.value) {
      wsCleanup.value()
      wsCleanup.value = null
    }
  }

  function getNodeOutput(nodeId) {
    return outputStreams.value.get(nodeId) || []
  }

  function getNodeCheckpoints(nodeId) {
    return checkpoints.value.get(nodeId) || []
  }

  function getNodeExecutionState(nodeId) {
    return executingNodes.value.get(nodeId) || null
  }

  function clearNodeState(nodeId) {
    executingNodes.value.delete(nodeId)
    outputStreams.value.delete(nodeId)
    checkpoints.value.delete(nodeId)
  }

  return {
    // State
    executingNodes,
    outputStreams,
    checkpoints,
    availableAgents,
    ecosystemGraph,
    domainsDetail,
    // Actions
    executeAgent,
    stopAgent,
    getAgentStatus,
    continueFromCheckpoint,
    sendChatMessage,
    approveCheckpoint,
    rejectCheckpoint,
    loadAgents,
    loadDomainsDetail,
    loadEcosystemGraph,
    appendOutput,
    handleWsMessage,
    setupWsListener,
    teardownWsListener,
    getNodeOutput,
    getNodeCheckpoints,
    getNodeExecutionState,
    clearNodeState
  }
})
