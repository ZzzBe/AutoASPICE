<template>
  <div
    class="tree-node"
    :class="{
      'tree-node--selected': isSelected,
      [`tree-node--${status}`]: true
    }"
    :style="{ paddingLeft: `${depth * 20 + 8}px` }"
    @click="$emit('select', node.id)"
    @contextmenu.prevent="showContextMenu"
  >
    <div class="tree-node-content">
      <el-icon
        class="tree-node-expand"
        v-if="hasChildren"
        @click.stop="$emit('toggle', node.id)"
      >
        <ArrowRight v-if="!expanded" />
        <ArrowDown v-else />
      </el-icon>
      <span v-else class="tree-node-expand-placeholder"></span>

      <span class="tree-node-icon status-icon" :title="statusLabel">
        <span v-if="status === 'pending'">&#9203;</span>
        <span v-else-if="status === 'running'">&#128260;</span>
        <span v-else-if="status === 'checkpoint'">&#128993;</span>
        <span v-else-if="status === 'completed'">&#9989;</span>
        <span v-else-if="status === 'failed'">&#10060;</span>
        <span v-else>&#9899;</span>
      </span>

      <span class="tree-node-name truncate">{{ node.name }}</span>

      <el-tag
        v-if="node.agent_name"
        size="small"
        type="info"
        class="tree-node-agent-tag"
      >
        {{ node.agent_name }}
      </el-tag>
    </div>

    <div v-if="hasChildren && expanded" class="tree-node-children">
      <TreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :selected-id="selectedId"
        @select="$emit('select', $event)"
        @toggle="$emit('toggle', $event)"
        @context-action="$emit('context-action', $event)"
      />
    </div>

    <!-- Context Menu -->
    <Teleport to="body">
      <div
        v-if="contextVisible"
        class="context-menu-overlay"
        @click="contextVisible = false"
      />
      <div
        v-if="contextVisible"
        class="context-menu"
        :style="contextMenuStyle"
      >
        <div class="context-menu-item" @click="handleAction('run')">
          <el-icon><VideoPlay /></el-icon>
          <span>Run Agent</span>
        </div>
        <div class="context-menu-item" @click="handleAction('stop')">
          <el-icon><VideoPause /></el-icon>
          <span>Stop Agent</span>
        </div>
        <div class="context-menu-item" @click="handleAction('view-output')">
          <el-icon><Document /></el-icon>
          <span>View Output</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item context-menu-item--danger" @click="handleAction('delete')">
          <el-icon><Delete /></el-icon>
          <span>Delete Node</span>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  node: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  selectedId: { type: String, default: null },
  expanded: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'toggle', 'context-action'])

const isSelected = computed(() => props.selectedId === props.node.id)
const hasChildren = computed(() => props.node.children && props.node.children.length > 0)
const status = computed(() => props.node.status || 'idle')

const statusLabel = computed(() => {
  const labels = {
    pending: 'Pending',
    running: 'Running',
    checkpoint: 'At Checkpoint',
    completed: 'Completed',
    failed: 'Failed',
    idle: 'Idle'
  }
  return labels[status.value] || 'Idle'
})

// Context menu
const contextVisible = ref(false)
const contextMenuStyle = ref({})

function showContextMenu(event) {
  contextVisible.value = true
  contextMenuStyle.value = {
    position: 'fixed',
    top: `${event.clientY}px`,
    left: `${event.clientX}px`,
    zIndex: 10000
  }
}

function handleAction(action) {
  contextVisible.value = false
  if (action === 'delete') {
    ElMessageBox.confirm(
      `Are you sure you want to delete "${props.node.name}"?`,
      'Delete Node',
      { confirmButtonText: 'Delete', cancelButtonText: 'Cancel', type: 'warning' }
    ).then(() => {
      emit('context-action', { action, nodeId: props.node.id })
    }).catch(() => {})
  } else {
    emit('context-action', { action, nodeId: props.node.id })
  }
}
</script>

<style scoped>
.tree-node {
  user-select: none;
}

.tree-node-content {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
  min-height: 30px;
}

.tree-node-content:hover {
  background: var(--color-bg-hover);
}

.tree-node--selected > .tree-node-content {
  background: rgba(88, 166, 255, 0.12);
  border-left: 2px solid var(--color-accent);
  margin-left: -2px;
}

.tree-node-expand {
  font-size: 12px;
  color: var(--color-text-muted);
  flex-shrink: 0;
  width: 16px;
}

.tree-node-expand-placeholder {
  width: 16px;
  flex-shrink: 0;
}

.tree-node-icon {
  font-size: 13px;
  flex-shrink: 0;
  width: 18px;
  text-align: center;
}

.tree-node-name {
  font-size: 13px;
  color: var(--color-text-primary);
  flex: 1;
  min-width: 0;
}

.tree-node-agent-tag {
  flex-shrink: 0;
  font-size: 10px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
}

.tree-node-children {
  /* children container */
}

.status-icon {
  font-size: 10px;
}

/* Context Menu */
.context-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
}

.context-menu {
  position: fixed;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 4px;
  min-width: 180px;
  z-index: 10000;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-primary);
  transition: background var(--transition-fast);
}

.context-menu-item:hover {
  background: var(--color-bg-hover);
}

.context-menu-item--danger {
  color: var(--color-error);
}

.context-menu-item--danger:hover {
  background: rgba(248, 81, 73, 0.1);
}

.context-menu-divider {
  height: 1px;
  background: var(--color-border);
  margin: 4px 8px;
}
</style>
