const axios = require('axios')
const fs = require('fs')

function register(ipcMain, config) {
  const baseUrl = config.PYTHON_BACKEND_URL

  // Upload a file by sending file content as base64
  ipcMain.handle('file:upload', async (_event, data) => {
    try {
      const { filePath, projectId } = data
      const fileBuffer = fs.readFileSync(filePath)
      const fileName = require('path').basename(filePath)
      const base64Content = fileBuffer.toString('base64')

      const response = await axios.post(`${baseUrl}/files/upload`, {
        file_name: fileName,
        content: base64Content,
        project_id: projectId
      })
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Read a file from the project workspace
  ipcMain.handle('file:read', async (_event, filePath) => {
    try {
      const response = await axios.get(`${baseUrl}/files/read`, {
        params: { path: filePath }
      })
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // Save a file to the project workspace
  ipcMain.handle('file:save', async (_event, data) => {
    try {
      const response = await axios.post(`${baseUrl}/files/save`, data)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || err.message
      }
    }
  })

  // List files in a project
  ipcMain.handle('file:list', async (_event, projectId) => {
    try {
      const response = await axios.get(`${baseUrl}/files/list`, {
        params: { project_id: projectId }
      })
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
