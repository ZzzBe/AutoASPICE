const electron = require('electron')
const { join } = require('path')
const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')
const axios = require('axios')

let mainWindow = null

function createWindow() {
  mainWindow = new electron.BrowserWindow({
    width: 1400,
    height: 900,
    show: false,
    title: 'AutoDev Studio',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true
    }
  })

  mainWindow.on('ready-to-show', () => mainWindow.show())
  mainWindow.webContents.setWindowOpenHandler(details => {
    electron.shell.openExternal(details.url)
    return { action: 'deny' }
  })

  const url = process.env.ELECTRON_RENDERER_URL || `file://${join(__dirname, '../renderer/index.html')}`
  mainWindow.loadURL(url)
}

// IPC handlers
electron.ipcMain.handle('agent:list', async () => {
  try { const r = await axios.get('http://localhost:5090/agent/list'); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('agent:ecosystem-graph', async () => {
  try { const r = await axios.get('http://localhost:5090/agent/ecosystem-graph'); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('agent:domains-detail', async () => {
  try { const r = await axios.get('http://localhost:5090/agent/domains-detail'); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('agent:status', async (_e, agentId) => {
  try { const r = await axios.get(`http://localhost:5090/agent/status/${agentId}`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('agent:execute', async (_e, data) => {
  try { const r = await axios.post('http://localhost:5090/agent/execute', data); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.response?.data?.detail || err.message } }
})
electron.ipcMain.handle('agent:stop', async (_e, agentId) => {
  try { const r = await axios.post(`http://localhost:5090/agent/stop/${agentId}`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('agent:checkpoint-continue', async (_e, data) => {
  try { const r = await axios.post(`http://localhost:5090/agent/checkpoint/${data.agentId}/continue`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('agent:checkpoint-chat', async (_e, data) => {
  try { const r = await axios.post(`http://localhost:5090/agent/checkpoint/${data.agentId}/chat`, { message: data.message }); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('agent:checkpoint-approve', async (_e, data) => {
  try { const { nodeId, reason } = data; const r = await axios.post(`http://localhost:5090/agent/checkpoint/${nodeId}/approve`, { reason }); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.response?.data?.detail || err.message } }
})
electron.ipcMain.handle('agent:checkpoint-reject', async (_e, data) => {
  try { const { nodeId, reason } = data; const r = await axios.post(`http://localhost:5090/agent/checkpoint/${nodeId}/reject`, { reason }); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.response?.data?.detail || err.message } }
})
electron.ipcMain.handle('agent:install', async (_e, data) => {
  try { const r = await axios.post('http://localhost:5090/agent/install', data); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.response?.data?.detail || err.message } }
})
electron.ipcMain.handle('agent:install-to-cache', async (_e, data) => {
  try { const r = await axios.post('http://localhost:5090/agent/install-to-cache', data); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.response?.data?.detail || err.message } }
})

electron.ipcMain.handle('project:list', async () => {
  try { const r = await axios.get('http://localhost:5090/projects'); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('project:create', async (_e, data) => {
  try { const r = await axios.post('http://localhost:5090/projects', data); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.response?.data?.detail || err.message } }
})
electron.ipcMain.handle('project:get', async (_e, projectId) => {
  try { const r = await axios.get(`http://localhost:5090/projects/${projectId}`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('project:delete', async (_e, projectId) => {
  try { const r = await axios.delete(`http://localhost:5090/projects/${projectId}`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('project:add-node', async (_e, data) => {
  try { const { projectId, node } = data; const r = await axios.post(`http://localhost:5090/projects/${projectId}/nodes`, node); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.response?.data?.detail || err.message } }
})
electron.ipcMain.handle('project:update-node', async (_e, data) => {
  try { const { projectId, nodeId, updates } = data; const r = await axios.put(`http://localhost:5090/projects/${projectId}/nodes/${nodeId}`, updates); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('project:remove-node', async (_e, data) => {
  try { const { projectId, nodeId } = data; const r = await axios.delete(`http://localhost:5090/projects/${projectId}/nodes/${nodeId}`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})

electron.ipcMain.handle('file:upload', async (_e, data) => {
  try {
    const buf = fs.readFileSync(data.filePath)
    const r = await axios.post('http://localhost:5090/files/upload', { file_name: path.basename(data.filePath), content: buf.toString('base64'), project_id: data.projectId })
    return { success: true, data: r.data }
  } catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('file:read', async (_e, filePath) => {
  try { const r = await axios.get('http://localhost:5090/files/read', { params: { path: filePath } }); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('file:save', async (_e, data) => {
  try { const r = await axios.post('http://localhost:5090/files/save', data); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('file:list', async (_e, projectId) => {
  try { const r = await axios.get('http://localhost:5090/files/list', { params: { project_id: projectId } }); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})

electron.ipcMain.handle('routing:analyze', async (_e, data) => {
  try { const r = await axios.post('http://localhost:5090/routing/analyze', data); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('routing:suggest', async (_e, data) => {
  try { const r = await axios.post('http://localhost:5090/routing/suggest', data); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})

electron.ipcMain.handle('audit:get-trail', async (_e, params) => {
  try { const { projectId, ...query } = params; const r = await axios.get(`http://localhost:5090/audit/${projectId}`, { params: query }); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('audit:get-node-audit', async (_e, data) => {
  try { const { projectId, nodeId } = data; const r = await axios.get(`http://localhost:5090/audit/${projectId}/nodes/${nodeId}`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})
electron.ipcMain.handle('audit:get-summary', async (_e, projectId) => {
  try { const r = await axios.get(`http://localhost:5090/audit/${projectId}/summary`); return { success: true, data: r.data } }
  catch (err) { return { success: false, error: err.message } }
})

electron.ipcMain.handle('dialog:openDirectory', async () => {
  if (!mainWindow) return null
  const result = await electron.dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] })
  return result.canceled ? null : result.filePaths[0]
})
electron.ipcMain.handle('app:getPath', () => electron.app.getAppPath())

// App lifecycle
electron.app.whenReady().then(() => {
  createWindow()
  electron.app.on('activate', () => { if (electron.BrowserWindow.getAllWindows().length === 0) createWindow() })
})

electron.app.on('window-all-closed', () => { if (process.platform !== 'darwin') electron.app.quit() })
