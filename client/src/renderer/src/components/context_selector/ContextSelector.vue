<template>
  <el-dialog
    v-model="visible"
    title="Select Context Files"
    width="600px"
    :close-on-click-modal="false"
  >
    <div class="context-selector-body">
      <div class="context-info">
        <el-icon><InfoFilled /></el-icon>
        <span>Select files from the project to include as context for the agent.</span>
      </div>

      <!-- Project file tree with checkboxes -->
      <div class="context-file-tree">
        <div class="context-section">
          <div class="context-section-title">Project Files</div>
          <el-tree
            ref="fileTreeRef"
            :data="fileTreeData"
            show-checkbox
            node-key="path"
            :default-checked-keys="preCheckedKeys"
            :props="treeProps"
            :default-expand-all="false"
            @check="handleCheck"
          >
            <template #default="{ data }">
              <div class="file-tree-node" @mouseenter="previewFile(data)" @mouseleave="hidePreview">
                <el-icon :size="14">
                  <Folder v-if="data.type === 'directory'" />
                  <Document v-else />
                </el-icon>
                <span>{{ data.name }}</span>
                <el-tag v-if="data.upstream" size="small" type="warning" class="upstream-tag">
                  upstream
                </el-tag>
              </div>
            </template>
          </el-tree>
        </div>

        <!-- Preview -->
        <div v-if="previewContent" class="context-preview">
          <div class="preview-header">
            <span>{{ previewFileName }}</span>
          </div>
          <div class="preview-content">
            <pre><code>{{ previewContent }}</code></pre>
          </div>
        </div>
      </div>

      <!-- Additional params -->
      <div class="context-params">
        <el-input
          v-model="additionalParams"
          type="textarea"
          :rows="2"
          placeholder="Additional instructions or parameters (optional)"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="handleCancel">Cancel</el-button>
      <el-button type="primary" @click="handleConfirm" :disabled="selectedFiles.length === 0">
        Start with Selected Context
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useProjectStore } from '../../store/project'

const props = defineProps({
  node: { type: Object, required: true },
  projectId: { type: String, required: true }
})

const emit = defineEmits(['confirm', 'cancel'])

const projectStore = useProjectStore()

const visible = ref(true)
const selectedFiles = ref([])
const previewContent = ref(null)
const previewFileName = ref('')
const additionalParams = ref('')
const fileTreeRef = ref(null)

const treeProps = {
  children: 'children',
  label: 'name'
}

// Build file tree from project files
const fileTreeData = computed(() => {
  const files = projectStore.files || []
  return buildFileTree(files)
})

// Pre-check upstream node outputs
const preCheckedKeys = computed(() => {
  const project = projectStore.currentProject
  if (!project) return []

  // Find nodes that are upstream of the current node
  // For simplicity, check parent nodes
  const keys = []
  const currentNode = props.node
  if (currentNode && currentNode.parent_id) {
    // Add any files associated with the parent node
    const parentNode = project.nodes.find((n) => n.id === currentNode.parent_id)
    if (parentNode) {
      ;(projectStore.files || []).forEach((file) => {
        if (file.node_id === parentNode.id) {
          keys.push(file.path)
        }
      })
    }
  }
  return keys
})

function buildFileTree(files) {
  const tree = []
  const map = new Map()

  files.forEach((file) => {
    const parts = (file.path || file.name || '').split('/')
    let currentPath = ''
    let parent = null

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const isLast = index === parts.length - 1

      if (!map.has(currentPath)) {
        const node = {
          name: part,
          path: currentPath,
          type: isLast ? 'file' : 'directory',
          children: [],
          upstream: file.node_id === props.node.parent_id
        }
        map.set(currentPath, node)

        if (parent) {
          parent.children.push(node)
        } else {
          tree.push(node)
        }
      }

      parent = map.get(currentPath)
    })
  })

  return tree
}

function handleCheck(checkedNode, checkedState) {
  selectedFiles.value = checkedState.checkedKeys.filter((key) => {
    const node = findNodeByPath(fileTreeData.value, key)
    return node && node.type === 'file'
  })
}

function findNodeByPath(nodes, path) {
  for (const node of nodes) {
    if (node.path === path) return node
    if (node.children) {
      const found = findNodeByPath(node.children, path)
      if (found) return found
    }
  }
  return null
}

async function previewFile(data) {
  if (data.type === 'directory') return
  previewFileName.value = data.name
  try {
    const result = await window.autodev.readFile(data.path)
    if (result.success) {
      const content = result.data?.content || result.data || ''
      previewContent.value = content.substring(0, 500) + (content.length > 500 ? '...' : '')
    }
  } catch {
    previewContent.value = '-- Preview unavailable --'
  }
}

function hidePreview() {
  // Keep preview visible; hover-based preview is optional
}

function handleConfirm() {
  emit('confirm', {
    files: selectedFiles.value,
    params: { instruction: additionalParams.value }
  })
  visible.value = false
}

function handleCancel() {
  visible.value = false
  emit('cancel')
}

watch(visible, (val) => {
  if (!val) emit('cancel')
})
</script>

<style scoped>
.context-selector-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.context-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(88, 166, 255, 0.08);
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.context-file-tree {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-height: 300px;
  overflow: hidden;
}

.context-section {
  overflow-y: auto;
}

.context-section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.file-tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.upstream-tag {
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 4px;
}

.context-preview {
  background: #0a0e14;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.preview-header {
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.preview-content {
  overflow-y: auto;
  flex: 1;
}

.preview-content pre {
  padding: 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.5;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.context-params {
  /* additional params input */
}
</style>
