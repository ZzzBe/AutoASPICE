<template>
  <div class="project-tree">
    <div class="project-tree-header">
      <div class="project-tree-title">
        <el-icon><FolderOpened /></el-icon>
        <span>{{ project?.name || 'Project' }}</span>
      </div>
      <el-button
        size="small"
        :icon="Plus"
        circle
        @click="handleAddNode"
        title="Add Node"
      />
    </div>

    <div class="project-tree-body">
      <!-- Loading -->
      <div v-if="loading" class="tree-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>

      <!-- Empty state -->
      <div v-else-if="nodes.length === 0" class="tree-empty">
        <el-icon :size="32"><Folder /></el-icon>
        <p>No nodes yet</p>
        <el-button size="small" type="primary" @click="handleAddNode">
          Add First Node
        </el-button>
      </div>

      <!-- Node tree -->
      <div v-else class="tree-nodes">
        <TreeNode
          v-for="node in nodes"
          :key="node.id"
          :node="node"
          :depth="0"
          :selected-id="selectedNode"
          :expanded="expandedNodes.has(node.id)"
          @select="handleSelect"
          @toggle="handleToggle"
          @context-action="handleContextAction"
        />
      </div>
    </div>

    <!-- File Browser Section -->
    <div class="tree-files-section">
      <div class="tree-files-header">
        <el-icon><Folder /></el-icon>
        <span>Files</span>
        <span class="file-count">{{ files.length }}</span>
      </div>
      <div class="tree-files-list">
        <div
          v-for="file in files"
          :key="file.path || file.name"
          class="tree-file-item"
          @click="handleFileClick(file)"
        >
          <el-icon><Document /></el-icon>
          <span class="truncate">{{ file.name || file.path }}</span>
        </div>
        <div v-if="files.length === 0" class="tree-empty-files">
          <span>No files uploaded</span>
        </div>
      </div>
    </div>

    <!-- Add Node Dialog -->
    <el-dialog v-model="showAddDialog" title="Add Node" width="500px">
      <el-form :model="newNode" label-position="top">
        <el-form-item label="Node Name">
          <el-input v-model="newNode.name" placeholder="e.g., Backend API Generator" />
        </el-form-item>
        <el-form-item label="Agent">
          <el-select v-model="newNode.agent_name" placeholder="Select an agent" style="width: 100%">
            <el-option
              v-for="agent in agentStore.availableAgents"
              :key="agent.id || agent.name"
              :label="agent.name"
              :value="agent.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Parent Node">
          <el-select v-model="newNode.parent_id" placeholder="None (root node)" clearable style="width: 100%">
            <el-option
              v-for="node in nodes"
              :key="node.id"
              :label="node.name"
              :value="node.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">Cancel</el-button>
        <el-button type="primary" @click="confirmAddNode" :disabled="!newNode.name">
          Add Node
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../../store/project'
import { useAgentStore } from '../../store/agent'
import TreeNode from './TreeNode.vue'

const projectStore = useProjectStore()
const agentStore = useAgentStore()

const props = defineProps({
  projectId: { type: String, required: true }
})

const project = computed(() => projectStore.currentProject)
const nodes = computed(() => projectStore.sortedNodes)
const selectedNode = computed(() => projectStore.selectedNode)
const loading = computed(() => projectStore.loading)
const files = computed(() => projectStore.files)

const expandedNodes = ref(new Set())
const showAddDialog = ref(false)
const newNode = ref({
  name: '',
  agent_name: '',
  parent_id: null
})

function handleSelect(nodeId) {
  projectStore.selectNode(nodeId)
}

function handleToggle(nodeId) {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
}

async function handleContextAction({ action, nodeId }) {
  switch (action) {
    case 'run':
      // Will be handled by AgentPanel
      projectStore.selectNode(nodeId)
      break
    case 'stop':
      try {
        await window.autodev.stopAgent(nodeId)
        ElMessage.success('Agent stopped')
      } catch (err) {
        ElMessage.error('Failed to stop agent')
      }
      break
    case 'view-output':
      projectStore.selectNode(nodeId)
      break
    case 'delete':
      try {
        await projectStore.removeNodeFromProject(props.projectId, nodeId)
        ElMessage.success('Node deleted')
      } catch (err) {
        ElMessage.error('Failed to delete node')
      }
      break
  }
}

function handleAddNode() {
  newNode.value = { name: '', agent_name: '', parent_id: null }
  showAddDialog.value = true
}

async function confirmAddNode() {
  if (!newNode.value.name) return
  try {
    await projectStore.addNodeToProject(props.projectId, {
      name: newNode.value.name,
      agent_name: newNode.value.agent_name || undefined,
      parent_id: newNode.value.parent_id || undefined
    })
    showAddDialog.value = false
    ElMessage.success('Node added')
  } catch (err) {
    ElMessage.error('Failed to add node')
  }
}

function handleFileClick(file) {
  // Emit open in deliverable view
  console.log('File clicked:', file)
}
</script>

<style scoped>
.project-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
}

.project-tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.project-tree-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.project-tree-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.tree-loading {
  display: flex;
  justify-content: center;
  padding: 24px;
  color: var(--color-text-muted);
}

.tree-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.tree-files-section {
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
  max-height: 200px;
  display: flex;
  flex-direction: column;
}

.tree-files-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.file-count {
  color: var(--color-text-muted);
  font-weight: 400;
}

.tree-files-list {
  overflow-y: auto;
  flex: 1;
}

.tree-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 20px;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.tree-file-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.tree-empty-files {
  padding: 12px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 12px;
}
</style>
