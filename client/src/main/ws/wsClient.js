const WebSocket = require('ws')
const { BrowserWindow } = require('electron')
const config = require('../config')

let ws = null
let currentProjectId = null
let currentNodeId = null
let reconnectTimer = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 10
const BASE_RECONNECT_DELAY = 1000

function getWsUrl(projectId, nodeId) {
  return `${config.WS_BACKEND_URL}/ws/${projectId}/${nodeId}`
}

function connect(projectId, nodeId) {
  // Disconnect any existing connection
  disconnect()

  currentProjectId = projectId
  currentNodeId = nodeId
  reconnectAttempts = 0

  const url = getWsUrl(projectId, nodeId)
  console.log(`[ws] Connecting to ${url}`)

  try {
    ws = new WebSocket(url)

    ws.on('open', () => {
      console.log(`[ws] Connected to ${url}`)
      reconnectAttempts = 0
      sendToRenderer('ws:message', {
        type: 'connection',
        status: 'connected',
        projectId,
        nodeId
      })
    })

    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString())
        sendToRenderer('ws:message', {
          type: 'output',
          projectId,
          nodeId,
          data: message
        })
      } catch (parseErr) {
        // Raw text message - forward as-is
        sendToRenderer('ws:message', {
          type: 'output',
          projectId,
          nodeId,
          data: { text: data.toString() }
        })
      }
    })

    ws.on('close', (code, reason) => {
      console.log(`[ws] Connection closed: ${code} ${reason}`)
      sendToRenderer('ws:message', {
        type: 'connection',
        status: 'disconnected',
        projectId,
        nodeId,
        code
      })
      scheduleReconnect(projectId, nodeId)
    })

    ws.on('error', (err) => {
      console.error(`[ws] Error: ${err.message}`)
      sendToRenderer('ws:message', {
        type: 'error',
        projectId,
        nodeId,
        error: err.message
      })
    })
  } catch (err) {
    console.error(`[ws] Failed to create WebSocket: ${err.message}`)
    scheduleReconnect(projectId, nodeId)
  }
}

function scheduleReconnect(projectId, nodeId) {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.log('[ws] Max reconnect attempts reached, giving up')
    sendToRenderer('ws:message', {
      type: 'connection',
      status: 'failed',
      projectId,
      nodeId,
      error: 'Max reconnection attempts reached'
    })
    return
  }

  const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts)
  reconnectAttempts++

  console.log(`[ws] Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`)

  reconnectTimer = setTimeout(() => {
    connect(projectId, nodeId)
  }, delay)
}

function disconnect() {
  currentProjectId = null
  currentNodeId = null

  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  if (ws) {
    ws.removeAllListeners()
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close()
    }
    ws = null
  }
}

function send(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(typeof data === 'string' ? data : JSON.stringify(data))
    return true
  }
  console.warn('[ws] Cannot send, not connected')
  return false
}

function isConnected() {
  return ws !== null && ws.readyState === WebSocket.OPEN
}

function sendToRenderer(channel, data) {
  const windows = BrowserWindow.getAllWindows()
  windows.forEach((win) => {
    if (!win.isDestroyed()) {
      win.webContents.send(channel, data)
    }
  })
}

module.exports = {
  connect,
  disconnect,
  send,
  isConnected
}
