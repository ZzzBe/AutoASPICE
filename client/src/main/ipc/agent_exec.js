const axios = require('axios')

function register(ipcMain, config) {
  const baseUrl = config.PYTHON_BACKEND_URL

  // Execute an agent on a node
  ipcMain.handle('agent:execute', async (_event, data) => {
    try {
      const response = await axios.post(`${baseUrl}/agent/execute`, data)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Stop agent execution
  ipcMain.handle('agent:stop', async (_event, agentId) => {
    try {
      const response = await axios.post(`${baseUrl}/agent/stop/${agentId}`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Get agent status
  ipcMain.handle('agent:status', async (_event, agentId) => {
    try {
      const response = await axios.get(`${baseUrl}/agent/status/${agentId}`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Continue from checkpoint
  ipcMain.handle('agent:checkpoint-continue', async (_event, data) => {
    try {
      const { agentId, checkpointId } = data
      const response = await axios.post(
        `${baseUrl}/agent/checkpoint/${agentId}/continue`,
        { checkpoint_id: checkpointId }
      )
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Chat at checkpoint
  ipcMain.handle('agent:checkpoint-chat', async (_event, data) => {
    try {
      const { agentId, checkpointId, message } = data
      const response = await axios.post(
        `${baseUrl}/agent/checkpoint/${agentId}/chat`,
        { checkpoint_id: checkpointId, message }
      )
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // List available agents
  ipcMain.handle('agent:list', async () => {
    try {
      const response = await axios.get(`${baseUrl}/agent/list`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Get ecosystem graph data
  ipcMain.handle('agent:ecosystem-graph', async () => {
    try {
      const response = await axios.get(`${baseUrl}/agent/ecosystem-graph`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })
}

module.exports = { register }
