const axios = require('axios')

function register(ipcMain, config) {
  const baseUrl = config.PYTHON_BACKEND_URL

  // Create a new project
  ipcMain.handle('project:create', async (_event, data) => {
    try {
      const response = await axios.post(`${baseUrl}/projects`, data)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // List all projects
  ipcMain.handle('project:list', async () => {
    try {
      const response = await axios.get(`${baseUrl}/projects`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Get a single project by ID
  ipcMain.handle('project:get', async (_event, projectId) => {
    try {
      const response = await axios.get(`${baseUrl}/projects/${projectId}`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Delete a project
  ipcMain.handle('project:delete', async (_event, projectId) => {
    try {
      const response = await axios.delete(`${baseUrl}/projects/${projectId}`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Add a node to a project
  ipcMain.handle('project:add-node', async (_event, data) => {
    try {
      const { projectId, node } = data
      const response = await axios.post(
        `${baseUrl}/projects/${projectId}/nodes`,
        node
      )
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Update a node in a project
  ipcMain.handle('project:update-node', async (_event, data) => {
    try {
      const { projectId, nodeId, updates } = data
      const response = await axios.put(
        `${baseUrl}/projects/${projectId}/nodes/${nodeId}`,
        updates
      )
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Remove a node from a project
  ipcMain.handle('project:remove-node', async (_event, data) => {
    try {
      const { projectId, nodeId } = data
      const response = await axios.delete(
        `${baseUrl}/projects/${projectId}/nodes/${nodeId}`
      )
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
