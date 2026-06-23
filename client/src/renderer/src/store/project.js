import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProjectStore = defineStore('project', () => {
  // ── State ───────────────────────────────────────────────────
  const currentProject = ref(null)
  const projects = ref([])
  const selectedNode = ref(null)
  const loading = ref(false)
  const files = ref([])

  // ── Getters ─────────────────────────────────────────────────
  const nodes = computed(() => currentProject.value?.nodes || [])
  const sortedNodes = computed(() => {
    return [...nodes.value].sort((a, b) => {
      const orderA = a.order ?? 999
      const orderB = b.order ?? 999
      return orderA - orderB
    })
  })

  const selectedNodeData = computed(() => {
    if (!selectedNode.value || !currentProject.value) return null
    return currentProject.value.nodes.find((n) => n.id === selectedNode.value) || null
  })

  // ── Actions ─────────────────────────────────────────────────
  async function loadProjects() {
    loading.value = true
    try {
      const result = await window.autodev.listProjects()
      if (result.success) {
        projects.value = result.data?.projects || result.data || []
      }
    } catch (err) {
      console.error('Failed to load projects:', err)
    } finally {
      loading.value = false
    }
  }

  async function createProject(data) {
    try {
      const result = await window.autodev.createProject(data)
      if (result.success) {
        const project = result.data
        projects.value.unshift(project)
        return project
      }
      throw new Error(result.error || 'Failed to create project')
    } catch (err) {
      console.error('Failed to create project:', err)
      throw err
    }
  }

  async function loadProject(id) {
    loading.value = true
    try {
      const result = await window.autodev.getProject(id)
      if (result.success) {
        currentProject.value = result.data
        // Also load files
        loadFiles(id)
        return result.data
      }
      throw new Error(result.error || 'Failed to load project')
    } catch (err) {
      console.error('Failed to load project:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteProject(id) {
    try {
      const result = await window.autodev.deleteProject(id)
      if (result.success) {
        projects.value = projects.value.filter((p) => p.id !== id)
        if (currentProject.value?.id === id) {
          currentProject.value = null
        }
        return true
      }
      throw new Error(result.error || 'Failed to delete project')
    } catch (err) {
      console.error('Failed to delete project:', err)
      throw err
    }
  }

  async function addNodeToProject(projectId, node) {
    try {
      const result = await window.autodev.addNode({ projectId, node })
      if (result.success) {
        if (currentProject.value?.id === projectId) {
          if (!currentProject.value.nodes) {
            currentProject.value.nodes = []
          }
          currentProject.value.nodes.push(result.data)
        }
        return result.data
      }
      throw new Error(result.error || 'Failed to add node')
    } catch (err) {
      console.error('Failed to add node:', err)
      throw err
    }
  }

  async function updateNodeStatus(projectId, nodeId, updates) {
    try {
      const result = await window.autodev.updateNode({
        projectId,
        nodeId,
        updates
      })
      if (result.success && currentProject.value?.id === projectId) {
        const node = currentProject.value.nodes.find((n) => n.id === nodeId)
        if (node) {
          Object.assign(node, updates)
        }
      }
      return result
    } catch (err) {
      console.error('Failed to update node:', err)
      throw err
    }
  }

  async function removeNodeFromProject(projectId, nodeId) {
    try {
      const result = await window.autodev.removeNode({ projectId, nodeId })
      if (result.success && currentProject.value?.id === projectId) {
        currentProject.value.nodes = currentProject.value.nodes.filter(
          (n) => n.id !== nodeId
        )
        if (selectedNode.value === nodeId) {
          selectedNode.value = null
        }
      }
      return result
    } catch (err) {
      console.error('Failed to remove node:', err)
      throw err
    }
  }

  function selectNode(nodeId) {
    selectedNode.value = nodeId
  }

  async function loadFiles(projectId) {
    try {
      const result = await window.autodev.listFiles(projectId)
      if (result.success) {
        files.value = result.data?.files || result.data || []
      }
    } catch (err) {
      console.error('Failed to load files:', err)
    }
  }

  return {
    // State
    currentProject,
    projects,
    selectedNode,
    loading,
    files,
    // Getters
    nodes,
    sortedNodes,
    selectedNodeData,
    // Actions
    loadProjects,
    createProject,
    loadProject,
    deleteProject,
    addNodeToProject,
    updateNodeStatus,
    removeNodeFromProject,
    selectNode,
    loadFiles
  }
})
