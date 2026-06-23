const axios = require('axios')

function register(ipcMain, config) {
  const baseUrl = config.PYTHON_BACKEND_URL

  // Analyze natural language instruction to determine routing
  ipcMain.handle('routing:analyze', async (_event, data) => {
    try {
      const response = await axios.post(`${baseUrl}/routing/analyze`, data)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Get available agent suggestions for a task
  ipcMain.handle('routing:suggest', async (_event, data) => {
    try {
      const response = await axios.post(`${baseUrl}/routing/suggest`, data)
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
