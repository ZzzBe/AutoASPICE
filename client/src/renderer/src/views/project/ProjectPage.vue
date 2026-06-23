<template>
  <div class="project-page">
    <!-- Top Command Bar -->
    <div class="project-top-bar">
      <CommandBar @use-suggestion="handleSuggestion" />
      <el-button size="small" class="audit-link-btn" @click="$router.push(`/audit/${projectId}`)">
        <el-icon><Clock /></el-icon>
        Audit Trail
      </el-button>
    </div>

    <!-- 3-Column Main Layout -->
    <div class="project-main">
      <!-- Left: Project Tree -->
      <aside class="project-left">
        <ProjectTree :project-id="projectId" />
      </aside>

      <!-- Center: Agent Panel -->
      <main class="project-center">
        <AgentPanel :project-id="projectId" />
      </main>

      <!-- Right: DeliverableView -->
      <aside class="project-right">
        <DeliverableView :files="deliverableFiles" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../../store/project'
import { useAgentStore } from '../../store/agent'
import CommandBar from '../../components/layout/CommandBar.vue'
import ProjectTree from '../../components/project_tree/ProjectTree.vue'
import AgentPanel from '../../components/agent_panel/AgentPanel.vue'
import DeliverableView from '../../components/deliverable_view/DeliverableView.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const agentStore = useAgentStore()

const projectId = computed(() => route.params.id)
const loading = ref(true)

const deliverableFiles = computed(() => {
  const node = projectStore.selectedNodeData
  if (!node?.deliverables) return []
  return node.deliverables.map((d) => ({
    name: d.name || d.path,
    path: d.path,
    content: d.content,
    type: d.type
  }))
})

onMounted(async () => {
  try {
    await projectStore.loadProject(projectId.value)
    // Connect WebSocket for real-time updates if a node is selected
    if (projectStore.selectedNode) {
      // WS connection is managed by the main process
    }
    loading.value = false
  } catch (err) {
    ElMessage.error('Failed to load project')
    router.push('/')
  }
})

onUnmounted(() => {
  // Clean up
  projectStore.selectNode(null)
})

async function handleSuggestion(suggestion) {
  const agentName = suggestion.agent_name || suggestion.agent_id || suggestion.name
  if (!agentName) return

  try {
    // Retrieve knowledge chunks from pipeline prepare step
    const knowledgeData = sessionStorage.getItem('autodev:pipeline:knowledge')
    let knowledgeChunks = []
    if (knowledgeData) {
      try { knowledgeChunks = JSON.parse(knowledgeData) } catch {}
    }

    const node = await projectStore.addNodeToProject(projectId.value, {
      name: agentName,
      agent_name: agentName,
      domain: suggestion.domain || '',
      workflow_steps: suggestion.workflow_steps || [],
      context_files: [],
      _knowledge_chunks: knowledgeChunks,
    })
    ElMessage.success(`Added node: ${agentName}`)

    // Select the newly created node
    if (node?.id) {
      projectStore.selectNode(node.id)
    }
  } catch (err) {
    ElMessage.error('Failed to add suggested node')
  }
}
</script>

<style scoped>
.project-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.project-top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 12px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  flex-shrink: 0;
}

.audit-link-btn {
  flex-shrink: 0;
}

.project-main {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  flex: 1;
  overflow: hidden;
}

.project-left {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.project-center {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.project-right {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Responsive: collapse right panel below 1200px */
@media (max-width: 1200px) {
  .project-main {
    grid-template-columns: 260px 1fr;
  }
  .project-right {
    display: none;
  }
}

/* Responsive: collapse to single column below 900px */
@media (max-width: 900px) {
  .project-main {
    grid-template-columns: 1fr;
  }
  .project-left {
    display: none;
  }
}
</style>
