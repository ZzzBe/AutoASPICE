<template>
  <div class="dashboard">
    <section class="dashboard-hero">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="hero-icon">&#9670;</span>
          {{ $t('common.appName') }}
        </h1>
        <p class="hero-subtitle">{{ $t('dashboard.hero.subtitle') }}</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="handleNewProject">
            <el-icon><Plus /></el-icon>
            {{ $t('dashboard.hero.newProject') }}
          </el-button>
          <el-button size="large" @click="$router.push('/agents')">
            <el-icon><MagicStick /></el-icon>
            {{ $t('dashboard.hero.browseAgents') }}
          </el-button>
        </div>
      </div>
    </section>

    <div class="dashboard-grid">
      <div class="dashboard-left">
        <section class="stats-section">
          <h3 class="section-title">{{ $t('dashboard.ecosystem') }}</h3>
          <div class="stats-cards">
            <div class="stat-card">
              <div class="stat-value">{{ ecosystemStats.agentCount }}</div>
              <div class="stat-label">{{ $t('dashboard.stats.agents') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ ecosystemStats.skillCount }}</div>
              <div class="stat-label">{{ $t('dashboard.stats.skills') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ ecosystemStats.workflowCount }}</div>
              <div class="stat-label">{{ $t('dashboard.stats.workflows') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ projects.length }}</div>
              <div class="stat-label">{{ $t('dashboard.stats.domains') }}</div>
            </div>
          </div>
        </section>

        <section class="projects-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('dashboard.recentProjects') }}</h3>
            <el-button size="small" text @click="loadProjects">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div v-if="projects.length === 0" class="section-empty">
            <p>{{ $t('dashboard.noProjects') }}</p>
          </div>
          <div v-else class="project-list">
            <div v-for="project in projects" :key="project.id" class="project-card" @click="$router.push(`/project/${project.id}`)">
              <div class="project-card-header">
                <el-icon><Folder /></el-icon>
                <span class="project-name">{{ project.name }}</span>
                <el-tag size="small" type="info">{{ $t('dashboard.agentNodes', { count: project.nodes?.length || 0 }) }}</el-tag>
              </div>
              <div class="project-card-meta">
                <span class="project-date">{{ formatDate(project.created_at) }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div class="dashboard-right">
        <section class="graph-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('dashboard.ecosystem') }}</h3>
            <el-input v-model="graphSearch" size="small" :placeholder="$t('common.search') + '...'" clearable class="graph-search-input">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>
          <div class="graph-container" ref="graphContainerRef">
            <div v-if="!graphLoaded" class="graph-loading">
              <el-icon class="is-loading" :size="24"><Loading /></el-icon>
              <span>{{ $t('common.loading') }}</span>
            </div>
            <div v-else-if="!hasGraphData" class="graph-empty">
              <p>{{ $t('common.noData') }}</p>
            </div>
          </div>
        </section>

        <section v-if="selectedGraphNode" class="node-detail">
          <div class="detail-header">
            <h4>{{ selectedGraphNode.name }}</h4>
            <el-tag size="small" :type="selectedGraphNode.type === 'agent' ? 'primary' : 'info'">
              {{ selectedGraphNode.type }}
            </el-tag>
          </div>
          <div class="detail-body">
            <p v-if="selectedGraphNode.description">{{ selectedGraphNode.description }}</p>
            <div class="detail-meta">
              <div v-if="selectedGraphNode.domain" class="meta-item">
                <span class="meta-label">{{ $t('agent.detail.domain') }}</span>
                <span class="meta-value">{{ selectedGraphNode.domain }}</span>
              </div>
            </div>
            <el-button v-if="selectedGraphNode.type === 'agent'" size="small" type="primary" @click="useAgent(selectedGraphNode)" class="use-agent-btn">
              {{ $t('agent.useAgent') }}
            </el-button>
          </div>
        </section>
      </div>
    </div>

    <el-dialog v-model="showNewProjectDialog" :title="$t('project.create')" width="500px">
      <el-form :model="newProject" label-position="top">
        <el-form-item :label="$t('project.name')">
          <el-input v-model="newProject.name" :placeholder="$t('project.namePlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNewProjectDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmNewProject" :disabled="!newProject.name">{{ $t('project.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../../store/project'
import { useAgentStore } from '../../store/agent'
import { t } from '../../i18n'

const router = useRouter()
const projectStore = useProjectStore()
const agentStore = useAgentStore()

const projects = computed(() => projectStore.projects)
const graphSearch = ref('')
const graphLoaded = ref(false)
const hasGraphData = ref(false)
const graphContainerRef = ref(null)
const selectedGraphNode = ref(null)
const showNewProjectDialog = ref(false)
let cyInstance = null

const newProject = ref({ name: '', description: '', agentName: '' })

const installedStats = ref({ agentCount: 0, skillCount: 0, workflowCount: 0, domainCount: 0 })
const ecosystemStats = computed(() => installedStats.value)

onMounted(async () => {
  await projectStore.loadProjects()
  const domainsData = await fetchDomainData()
  if (domainsData) {
    computeInstalledStats(domainsData)
    buildGraphElements(domainsData)
  }
})

let cachedDomainData = null

async function fetchDomainData() {
  if (cachedDomainData) return cachedDomainData
  try {
    const r = await fetch('http://localhost:5090/agent/domains-detail')
    const d = await r.json()
    cachedDomainData = d
    return d
  } catch { return null }
}

function computeInstalledStats(d) {
  let agents = 0, skills = 0, workflows = 0, domains = 0
  for (const dom of d.domains || []) {
    agents += dom.agents?.filter(a => a.installed).length || 0
    skills += dom.skills?.filter(s => s.installed).length || 0
    workflows += dom.workflows?.filter(w => w.installed).length || 0
    const hasInstalled = (dom.agents || []).some(a => a.installed)
    if (hasInstalled) domains++
  }
  installedStats.value = { agentCount: agents, skillCount: skills, workflowCount: workflows, domainCount: domains }
}

async function buildGraphElements(d) {
  graphLoaded.value = false
  try {
    const elements = []
    for (const dom of (d.domains || [])) {
      const installedAgents = (dom.agents || []).filter(a => a.installed)
      const installedSkills = (dom.skills || []).filter(s => s.installed)
      const installedWfs = (dom.workflows || []).filter(w => w.installed)
      if (!installedAgents.length && !installedSkills.length) continue
      // Domain node
      elements.push({ data: { id: `domain-${dom.name}`, label: dom.name, type: 'domain', agent_count: dom.agent_count }})
      for (const a of installedAgents) {
        elements.push({ data: { id: `agent-${a.name}`, label: a.name, type: 'agent', domain: dom.name, parent: `domain-${dom.name}` }})
      }
      for (const s of installedSkills) {
        elements.push({ data: { id: `skill-${s.name}`, label: s.name, type: 'skill', domain: dom.name, parent: `domain-${dom.name}` }})
      }
      for (const w of installedWfs) {
        elements.push({ data: { id: `wf-${w.name}`, label: w.name, type: 'workflow', domain: dom.name, parent: `domain-${dom.name}` }})
      }
      // Edges: domain → agents/skills/workflows
      for (const a of installedAgents) {
        elements.push({ data: { id: `e-da-${a.name}`, source: `domain-${dom.name}`, target: `agent-${a.name}` }})
      }
      // Agent → Skill dependencies
      for (const e of (dom.dependency_edges || [])) {
        if (installedAgents.some(a => a.name === e.source) && installedSkills.some(s => s.name === e.target)) {
          elements.push({ data: { id: `e-as-${e.source}-${e.target}`, source: `agent-${e.source}`, target: `skill-${e.target}`, type: 'calls' }})
        }
      }
      // Agent → Workflow (same agent)
      for (const w of installedWfs) {
        if (installedAgents.some(a => a.name === w.agent)) {
          elements.push({ data: { id: `e-aw-${w.agent}-${w.name}`, source: `agent-${w.agent}`, target: `wf-${w.name}`, type: 'orchestrates' }})
        }
      }
    }
    hasGraphData.value = elements.length > 0
    if (hasGraphData.value) {
      await nextTick()
      initCytoscape(elements)
    }
  } catch { hasGraphData.value = false }
  graphLoaded.value = true
}

function initCytoscape(elements) {
  if (!graphContainerRef.value || !elements?.length) return
  import('cytoscape').then(cyto => {
    cyInstance = cyto.default({
      container: graphContainerRef.value,
      elements: elements,
      style: [
        { selector: 'node', style: { 'background-color': '#30363d', label: 'data(label)', 'font-size': '10px', color: '#e6edf3', width: 50, height: 50 } },
        { selector: 'node[type="agent"]', style: { 'background-color': '#1f6feb', width: 55, height: 55 } },
        { selector: 'node[type="skill"]', style: { 'background-color': '#238636', width: 40, height: 40 } },
        { selector: 'node.highlighted', style: { 'border-color': '#f0883e', 'border-width': 3 } },
        { selector: 'edge', style: { width: 1.5, 'line-color': '#484f58', 'target-arrow-color': '#484f58', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } }
      ],
      layout: { name: 'grid' },
      wheelSensitivity: 0.3, minZoom: 0.3, maxZoom: 2.5
    })
    cyInstance.on('tap', 'node', evt => {
      const node = evt.target
      selectedGraphNode.value = { id: node.id(), name: node.data('label'), type: node.data('type'), description: node.data('description'), domain: node.data('domain') }
    })
    cyInstance.on('tap', evt => { if (evt.target === cyInstance) { selectedGraphNode.value = null; cyInstance.elements().removeClass('highlighted') } })
  })
}

function useAgent(agentNode) { newProject.value = { name: '', description: '', agentName: agentNode.name || agentNode.id }; showNewProjectDialog.value = true }
function handleNewProject() { newProject.value = { name: '', description: '', agentName: '' }; showNewProjectDialog.value = true }

async function confirmNewProject() {
  try {
    const project = await projectStore.createProject({ name: newProject.value.name, description: newProject.value.description })
    if (newProject.value.agentName && project) await projectStore.addNodeToProject(project.id, { name: newProject.value.agentName, agent_name: newProject.value.agentName })
    showNewProjectDialog.value = false
    ElMessage.success(t('project.create'))
    router.push(`/project/${project.id}`)
  } catch (err) { ElMessage.error(err.message || 'Failed') }
}

function formatDate(d) { if (!d) return ''; return new Date(d).toLocaleDateString() }
async function loadProjects() { await projectStore.loadProjects() }

watch(graphSearch, term => {
  if (!cyInstance) return
  cyInstance.elements().removeClass('highlighted')
  if (!term) return
  const lower = term.toLowerCase()
  cyInstance.nodes().forEach(node => { const label = (node.data('label') || '').toLowerCase(); if (label.includes(lower)) node.addClass('highlighted') })
})
</script>

<style scoped>
.dashboard { height: 100%; overflow-y: auto; padding: 24px 32px; }
.dashboard-hero { margin-bottom: 32px; padding: 32px 0; border-bottom: 1px solid var(--color-border); }
.hero-content { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; }
.hero-title { font-size: 28px; font-weight: 700; color: var(--color-text-primary); display: flex; align-items: center; gap: 12px; }
.hero-icon { color: var(--color-accent); font-size: 32px; }
.hero-subtitle { font-size: 15px; color: var(--color-text-secondary); max-width: 500px; line-height: 1.5; }
.hero-actions { display: flex; gap: 12px; margin-top: 8px; }
.dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.section-title { font-size: 14px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 12px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-empty { padding: 24px; text-align: center; color: var(--color-text-muted); background: var(--color-bg-secondary); border-radius: var(--radius-md); border: 1px solid var(--color-border); font-size: 13px; }
.stats-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.stat-card { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 16px; text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--color-accent); font-family: var(--font-mono); }
.stat-label { font-size: 11px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
.project-list { display: flex; flex-direction: column; gap: 8px; }
.project-card { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px 16px; cursor: pointer; transition: all var(--transition-fast); }
.project-card:hover { border-color: var(--color-accent); background: var(--color-bg-hover); }
.project-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.project-name { font-size: 14px; font-weight: 500; color: var(--color-text-primary); flex: 1; }
.project-card-meta { font-size: 11px; color: var(--color-text-muted); padding-left: 24px; }
.graph-section { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 16px; margin-bottom: 16px; }
.graph-search-input { width: 200px; }
.graph-container { width: 100%; height: 350px; background: #0a0e14; border-radius: var(--radius-sm); overflow: hidden; }
.graph-loading, .graph-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 8px; color: var(--color-text-muted); font-size: 13px; }
.node-detail { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 16px; }
.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.detail-header h4 { font-size: 15px; font-weight: 600; color: var(--color-text-primary); }
.detail-body p { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 12px; line-height: 1.5; }
.detail-meta { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.meta-item { display: flex; align-items: baseline; gap: 8px; font-size: 12px; }
.meta-label { color: var(--color-text-muted); min-width: 80px; }
.meta-value { color: var(--color-text-primary); }
.use-agent-btn { margin-top: 4px; }
</style>
