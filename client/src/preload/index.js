const { contextBridge, ipcRenderer } = require('electron')

const autodev = {
  // Agent Execution
  installAgent: (data) => ipcRenderer.invoke('agent:install', data),
  installAgentToCache: (data) => ipcRenderer.invoke('agent:install-to-cache', data),
  executeAgent: (data) => ipcRenderer.invoke('agent:execute', data),
  stopAgent: (agentId) => ipcRenderer.invoke('agent:stop', agentId),
  getAgentStatus: (agentId) => ipcRenderer.invoke('agent:status', agentId),
  checkpointContinue: (data) => ipcRenderer.invoke('agent:checkpoint-continue', data),
  checkpointChat: (data) => ipcRenderer.invoke('agent:checkpoint-chat', data),
  approveCheckpoint: (data) => ipcRenderer.invoke('agent:checkpoint-approve', data),
  rejectCheckpoint: (data) => ipcRenderer.invoke('agent:checkpoint-reject', data),
  listAgents: () => ipcRenderer.invoke('agent:list'),
  getDomainDetail: () => ipcRenderer.invoke('agent:domains-detail'),
  getEcosystemGraph: () => ipcRenderer.invoke('agent:ecosystem-graph'),

  // Projects
  createProject: (data) => ipcRenderer.invoke('project:create', data),
  listProjects: () => ipcRenderer.invoke('project:list'),
  getProject: (id) => ipcRenderer.invoke('project:get', id),
  deleteProject: (id) => ipcRenderer.invoke('project:delete', id),
  addNode: (data) => ipcRenderer.invoke('project:add-node', data),
  updateNode: (data) => ipcRenderer.invoke('project:update-node', data),
  removeNode: (data) => ipcRenderer.invoke('project:remove-node', data),

  // Files
  uploadFile: (data) => ipcRenderer.invoke('file:upload', data),
  readFile: (path) => ipcRenderer.invoke('file:read', path),
  saveFile: (data) => ipcRenderer.invoke('file:save', data),
  listFiles: (projectId) => ipcRenderer.invoke('file:list', projectId),

  // Routing
  analyzeRouting: (data) => ipcRenderer.invoke('routing:analyze', data),
  suggestRouting: (data) => ipcRenderer.invoke('routing:suggest', data),

  // Audit
  getAuditTrail: (params) => ipcRenderer.invoke('audit:get-trail', params),
  getNodeAudit: (data) => ipcRenderer.invoke('audit:get-node-audit', data),
  getAuditSummary: (projectId) => ipcRenderer.invoke('audit:get-summary', projectId),

  // WebSocket events
  onWsMessage: (callback) => {
    const handler = (_event, data) => callback(data)
    ipcRenderer.on('ws:message', handler)
    return () => ipcRenderer.removeListener('ws:message', handler)
  },
  removeWsListener: () => ipcRenderer.removeAllListeners('ws:message'),

  // Utility
  selectDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  getAppPath: () => ipcRenderer.invoke('app:getPath')
}

contextBridge.exposeInMainWorld('autodev', autodev)
