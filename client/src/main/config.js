const path = require('path')
const { app } = require('electron')

const PYTHON_BACKEND_URL = 'http://localhost:5090'
const WS_BACKEND_URL = 'ws://localhost:5090'

function getBackendPath() {
  const isDev = !app.isPackaged
  if (isDev) {
    return path.resolve(__dirname, '../../../../backend')
  }
  return path.resolve(process.resourcesPath, 'backend')
}

function getPythonCommand() {
  // On macOS/Linux, prefer python3; on Windows, prefer python
  if (process.platform === 'win32') {
    return 'python'
  }
  return 'python3'
}

function getHealthCheckUrl() {
  return `${PYTHON_BACKEND_URL}/health`
}

module.exports = {
  PYTHON_BACKEND_URL,
  WS_BACKEND_URL,
  getBackendPath,
  getPythonCommand,
  getHealthCheckUrl
}
