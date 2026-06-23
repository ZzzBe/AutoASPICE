<template>
  <div class="agent-market">
    <!-- ══════ Domain List (Level 1) ══════ -->
    <template v-if="!selectedDomain">
      <div class="market-header">
        <h2>{{ $t('agent.title') }}</h2>
        <p>{{ domainCount }} domains · {{ totalAgents }} agents · {{ totalSkills }} skills</p>
        <el-input v-model="searchQuery" :placeholder="$t('common.search') + '...'"
          clearable class="market-search" size="large">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>

      <div v-if="loading" class="market-loading">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <span>{{ $t('common.loading') }}</span>
      </div>

      <div v-else class="domain-grid">
        <div v-for="d in filteredDomains" :key="d.name" class="domain-card"
          @click="openDomain(d)">
          <div class="domain-card-top">
            <div class="domain-icon">
              <el-icon :size="22"><FolderOpened /></el-icon>
            </div>
            <div class="domain-info">
              <h3 class="domain-name">{{ domainLabel(d.name) }}</h3>
              <span class="domain-key">{{ d.name }}</span>
            </div>
          </div>
          <div class="domain-stats">
            <div class="dstat">
              <span class="dstat-val">{{ d.agent_count }}</span>
              <span class="dstat-lbl">Agents</span>
            </div>
            <div class="dstat-divider"></div>
            <div class="dstat">
              <span class="dstat-val">{{ d.skill_count }}</span>
              <span class="dstat-lbl">Skills</span>
            </div>
            <div class="dstat-divider"></div>
            <div class="dstat">
              <span class="dstat-val">{{ d.workflow_count || 0 }}</span>
              <span class="dstat-lbl">WFs</span>
            </div>
          </div>
          <div class="domain-card-footer">
            <el-icon><ArrowRight /></el-icon>
            <span>{{ $t('agent.viewDetails') }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ══════ Domain Detail (Level 2) ══════ -->
    <template v-else>
      <div class="detail-header-bar">
        <el-button text @click="selectedDomain = null">
          <el-icon><ArrowLeft /></el-icon> {{ $t('common.back') }}
        </el-button>
        <h2>{{ domainLabel(selectedDomain.name) }}</h2>
        <el-tag size="large" effect="dark">{{ selectedDomain.agent_count }} Agents · {{ selectedDomain.skill_count }} Skills · {{ selectedDomain.workflow_count || 0 }} Workflows</el-tag>
      </div>

      <div class="detail-panels">
        <!-- ── Agents Column ── -->
        <div class="detail-col agents-col">
          <h3 class="col-title">
            <el-icon><MagicStick /></el-icon> Agents ({{ selectedDomain.agents.length }})
          </h3>
          <div v-if="selectedDomain.agents.length === 0" class="col-empty">
            {{ $t('common.noData') }}
          </div>
          <div v-else class="agent-list">
            <div v-for="agent in selectedDomain.agents" :key="agent.name"
              class="agent-item"
              :class="{ highlighted: hoveredAgent === agent.name }"
              @mouseenter="hoveredAgent = agent.name"
              @mouseleave="hoveredAgent = null"
              @click="selectAgent(agent)"
            >
              <div class="agent-item-header">
                <span class="agent-item-name">{{ agent.name }}</span>
                <el-tag v-if="agent.capability_count" size="small" type="info" effect="plain">
                  {{ agent.capability_count }} {{ $t('agent.capabilities') }}
                </el-tag>
              </div>
              <div class="agent-item-author" v-if="agent.author">
                <el-icon :size="12"><User /></el-icon>
                <span>{{ agent.author }}</span>
              </div>
              <p class="agent-item-desc">{{ agent.description || $t('agent.noDescription') }}</p>
              <!-- Dependency badges: agent's required skills -->
              <div class="agent-skill-links" v-if="getAgentSkills(agent.name).length">
                <span class="link-label">→ {{ $t('agent.skills') }}:</span>
                <el-tag v-for="sn in getAgentSkills(agent.name)" :key="sn"
                  size="small" type="success" effect="plain"
                  class="skill-link-tag"
                  @click.stop="scrollToSkill(sn)">
                  {{ sn }}
                </el-tag>
              </div>
              <div class="agent-item-actions">
                <el-button v-if="!agent.installed" size="small" type="success"
                  :loading="installingAgent === agent.name"
                  @click.stop="installAgent(agent)">
                  ⬇ {{ $t('agent.install') }}
                </el-button>
                <el-tag v-else size="small" type="success" effect="dark">
                  ✅ {{ $t('agent.installed') }}
                </el-tag>
                <el-button v-if="agent.installed" size="small" type="primary" @click.stop="useAgent(agent)">
                  {{ $t('agent.useAgent') }}
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Skills Column ── -->
        <div class="detail-col skills-col">
          <h3 class="col-title">
            <el-icon><SetUp /></el-icon> Skills ({{ selectedDomain.skills.length }})
          </h3>
          <div v-if="selectedDomain.skills.length === 0" class="col-empty">
            {{ $t('common.noData') }}
          </div>
          <div v-else class="skill-list">
            <div v-for="skill in selectedDomain.skills" :key="skill.name"
              :id="'skill-' + skill.name"
              class="skill-item"
              :class="{ 'linked-by-agent': isSkillLinked(skill.name) }"
            >
              <div class="skill-item-header">
                <span class="skill-item-name">{{ skill.name }}</span>
                <el-tag v-if="skill.installed" size="small" type="success" effect="plain" class="skill-status-tag">
                  ✅ {{ $t('agent.installed') }}
                </el-tag>
                <el-button v-else size="small" type="success" text
                  class="skill-download-btn"
                  @click.stop="installSkill(skill)">
                  ⬇ {{ $t('agent.install') }}
                </el-button>
              </div>
              <div class="agent-item-author" v-if="skill.author">
                <el-icon :size="12"><User /></el-icon>
                <span>{{ skill.author }}</span>
              </div>
              <p class="skill-item-desc">{{ skill.description || 'Skill for ' + skill.name }}</p>
              <!-- Reverse dependency: which agents use this skill -->
              <div class="skill-agent-links" v-if="skill.used_by?.length">
                <span class="link-label">← Used by:</span>
                <el-tag v-for="an in skill.used_by" :key="an"
                  size="small" type="primary" effect="plain"
                  class="agent-link-tag"
                  @click.stop="scrollToAgent(an)">
                  {{ an }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Workflows Column ── -->
        <div class="detail-col workflows-col">
          <h3 class="col-title">
            <el-icon><Share /></el-icon> Workflows ({{ (selectedDomain.workflows || []).length }})
          </h3>
          <div v-if="!selectedDomain.workflows?.length" class="col-empty">
            {{ $t('common.noData') }}
          </div>
          <div v-else class="workflow-list">
            <div v-for="wf in selectedDomain.workflows" :key="wf.name"
              class="workflow-item">
              <div class="workflow-item-header">
                <span class="workflow-item-name">{{ wf.name }}</span>
                <el-tag size="small" type="warning" effect="plain">{{ wf.steps || 0 }} steps</el-tag>
              </div>
              <p class="workflow-item-desc">{{ wf.description || '' }}</p>
              <div class="workflow-agent-link">
                <span class="link-label">🧑 Agent:</span>
                <el-tag size="small" type="primary" effect="plain">{{ wf.agent }}</el-tag>
              </div>
              <el-tag v-if="wf.installed" size="small" type="success" effect="dark" class="wf-status">
                ✅ {{ $t('agent.installed') }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ══════ Agent Detail Dialog ══════ -->
    <el-dialog v-model="showDetail" :title="detailAgent?.name" width="650px">
      <template v-if="detailAgent">
        <div class="detail-section" v-if="detailAgent.author">
          <h4>{{ $t('agent.detail.author') || 'Author' }}</h4>
          <p><el-icon :size="14"><User /></el-icon> {{ detailAgent.author }}</p>
        </div>
        <div class="detail-section" v-if="detailAgent.description">
          <h4>{{ $t('agent.detail.description') }}</h4>
          <p>{{ detailAgent.description }}</p>
        </div>
        <div class="detail-section" v-if="detailAgent.capabilities?.length">
          <h4>{{ $t('agent.detail.capabilities') }}</h4>
          <div class="tag-list">
            <el-tag v-for="cap in detailAgent.capabilities" :key="cap" size="small">{{ cap }}</el-tag>
          </div>
        </div>
        <div class="detail-section" v-if="detailAgent.expertise_areas?.length">
          <h4>{{ $t('agent.detail.expertise') }}</h4>
          <div class="tag-list">
            <el-tag v-for="exp in detailAgent.expertise_areas" :key="exp" size="small" type="success">{{ exp }}</el-tag>
          </div>
        </div>
        <div class="detail-section" v-if="detailAgent.tool_dependencies?.length">
          <h4>{{ $t('agent.detail.toolDependencies') }}</h4>
          <div class="tag-list">
            <el-tag v-for="tool in detailAgent.tool_dependencies" :key="tool" size="small" type="info">{{ tool }}</el-tag>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="showDetail = false">{{ $t('common.close') }}</el-button>
        <el-button type="primary" @click="useAgent(detailAgent); showDetail = false">
          {{ $t('agent.useAgent') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ══════ Use Agent Dialog ══════ -->
    <el-dialog v-model="showUseDialog" :title="$t('agent.useAgent')" width="500px">
      <el-form label-position="top">
        <el-form-item :label="$t('project.name')">
          <el-input v-model="useProjectName" :placeholder="$t('project.namePlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUseDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmUseAgent" :disabled="!useProjectName">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../../store/project'
import { useAgentStore } from '../../store/agent'
import { t } from '../../i18n'

const router = useRouter()
const projectStore = useProjectStore()
const agentStore = useAgentStore()

const searchQuery = ref('')
const loading = ref(false)
const domains = ref([])
const selectedDomain = ref(null)
const hoveredAgent = ref(null)

const showDetail = ref(false)
const detailAgent = ref(null)
const showUseDialog = ref(false)
const useProjectName = ref('')
const useTargetAgent = ref(null)

const totalAgents = computed(() => domains.value.reduce((s, d) => s + d.agent_count, 0))
const totalSkills = computed(() => domains.value.reduce((s, d) => s + d.skill_count, 0))
const domainCount = computed(() => domains.value.length)

const filteredDomains = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return domains.value
  return domains.value.filter(d =>
    d.name.toLowerCase().includes(q) ||
    (domainLabel(d.name) || '').toLowerCase().includes(q) ||
    d.agents.some(a => a.name.toLowerCase().includes(q)) ||
    d.skills.some(s => s.name.toLowerCase().includes(q))
  )
})

const DOMAIN_NAMES = {
  adas: 'ADAS/自动驾驶', 'functional-safety': '功能安全', sotif: 'SOTIF预期功能安全',
  autosar: 'AUTOSAR架构', diagnostics: '诊断系统', cybersecurity: '网络安全',
  safety: '功能安全', security: '信息安全', powertrain: '动力总成',
  battery: '电池管理', v2x: 'V2X车联网', cloud: '云端平台',
  testing: '测试验证', calibration: '标定测量', mbd: '模型化设计',
  embedded: '嵌入式系统', network: '车载网络', 'ai-ecu': 'AI边缘计算',
  orchestration: '编排引擎', 'project-management': '项目管理',
  oem: '整车厂OEM', tier1: '一级供应商', tier2: '二级供应商',
  cockpit: '智能座舱', 'ev-systems': '电驱系统', 'ml-analytics': '机器学习',
  'vehicle-systems': '车辆系统', 'sdv-platform': 'SDV平台',
  'zonal-architecture': '区域架构', 'hpc-platform': '高性能计算',
  'powertrain-chassis': '底盘动力', qnx: 'QNX RTOS', logging: '诊断日志',
  services: '服务', specialists: '专家', tools: '工具',
  'product-owner': '产品', toolchain: '工具链', 'hardware-safety': '硬件安全',
  kubernetes: 'K8s', 'automotive-workflow': '工作流', core: '核心路由',
}

const installingAgent = ref(null)

function domainLabel(key) { return DOMAIN_NAMES[key] || key }

async function refreshDomains() {
  try {
    const r = await fetch('http://localhost:5090/agent/domains-detail')
    const d = await r.json()
    if (d.domains?.length) {
      domains.value = d.domains
      // Re-apply current selected domain
      if (selectedDomain.value) {
        selectedDomain.value = d.domains.find(x => x.name === selectedDomain.value.name) || null
      }
    }
  } catch (e) { console.error('Refresh failed:', e) }
}

async function installAgent(agent) {
  installingAgent.value = agent.name
  try {
    const r = await fetch('http://localhost:5090/agent/download', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_name: agent.name })
    })
    const result = await r.json()

    if (result?.agent_downloaded !== false) {
      const parts = []
      if (result.skills_downloaded) parts.push(`${result.skills_downloaded}/${result.skills_total} skills`)
      if (result.workflows_downloaded) parts.push(`${result.workflows_downloaded} workflows`)
      const errs = result.errors?.length ? ` (${result.errors.length} errors)` : ''
      ElMessage.success(`${agent.name} downloaded: ${parts.join(', ')}${errs}`)
      await refreshDomains()
    } else if (result?.errors?.length) {
      ElMessage.error(`Download failed: ${result.errors[0]}`)
    } else {
      ElMessage.warning(`${agent.name}: nothing to download`)
    }
  } catch (e) { ElMessage.error('Download failed: ' + (e.message || e)) }
  finally { installingAgent.value = null }
}

function installSkill(skill) {
  // Skills are auto-installed when their parent agent is installed
  // For standalone skill install, find first agent that uses it and install that agent
  const agents = selectedDomain.value?.agents || []
  const parent = agents.find(a =>
    (selectedDomain.value?.dependency_edges || []).some(e => e.source === a.name && e.target === skill.name)
  )
  if (parent) installAgent(parent)
  else ElMessage.info('This skill has no parent agent. Use "Add Agent" to install it.')
}

onMounted(async () => {
  loading.value = true
  try {
    console.log('[AgentMarket] Fetching domains from API...')
    const r = await fetch('http://localhost:5090/agent/domains-detail')
    console.log('[AgentMarket] Fetch response:', r.status)
    const d = await r.json()
    console.log('[AgentMarket] Got domains:', d.domains?.length)
    if (d.domains?.length) {
      domains.value = d.domains
    }
  } catch (e) {
    console.error('[AgentMarket] Fetch failed:', e.message || e)
    // Electron IPC fallback
    try {
      if (window.autodev?.getDomainDetail) {
        const result = await window.autodev.getDomainDetail()
        if (result?.success) domains.value = result.data?.domains || []
      }
    } catch (e2) { console.warn('IPC also failed:', e2) }
  }
  loading.value = false
})

function openDomain(d) { selectedDomain.value = d }

function getAgentSkills(agentName) {
  if (!selectedDomain.value) return []
  return selectedDomain.value.dependency_edges
    .filter(e => e.source === agentName)
    .map(e => e.target)
}

function isSkillLinked(skillName) {
  if (!hoveredAgent.value) return false
  return getAgentSkills(hoveredAgent.value).includes(skillName)
}

function scrollToSkill(skillName) {
  const el = document.getElementById('skill-' + skillName)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function scrollToAgent(agentName) {
  // Highlight and scroll to agent
  hoveredAgent.value = agentName
  setTimeout(() => { hoveredAgent.value = null }, 3000)
}

function selectAgent(agent) { detailAgent.value = agent; showDetail.value = true }
function useAgent(agent) { useTargetAgent.value = agent; useProjectName.value = agent?.name + ' Project'; showUseDialog.value = true }

async function confirmUseAgent() {
  showUseDialog.value = false
  const agent = useTargetAgent.value
  if (!agent) return
  try {
    const project = await projectStore.createProject({ name: useProjectName.value })
    try { await window.autodev.installAgent({ agent_name: agent.name, project_id: project.id }) } catch {}
    await projectStore.addNodeToProject(project.id, { name: agent.name, agent_name: agent.name })
    ElMessage.success(t('project.addNode'))
    router.push(`/project/${project.id}`)
  } catch (err) { ElMessage.error(err.message || 'Failed') }
}
</script>

<style scoped>
.agent-market { height: 100%; overflow-y: auto; padding: 24px 32px; }
.market-header { margin-bottom: 24px; }
.market-header h2 { font-size: 22px; font-weight: 700; color: var(--color-text-primary); margin-bottom: 4px; }
.market-header p { font-size: 13px; color: var(--color-text-muted); margin-bottom: 16px; }
.market-search { max-width: 400px; }
.market-loading { display: flex; flex-direction: column; align-items: center; padding: 64px; gap: 12px; color: var(--color-text-muted); }

/* ── Domain Grid ── */
.domain-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
.domain-card { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 20px; cursor: pointer; transition: all var(--transition-fast); display: flex; flex-direction: column; gap: 14px; }
.domain-card:hover { border-color: var(--color-accent); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.domain-card-top { display: flex; align-items: flex-start; gap: 12px; }
.domain-icon { width: 40px; height: 40px; border-radius: var(--radius-md); background: rgba(88,166,255,0.1); display: flex; align-items: center; justify-content: center; color: var(--color-accent); flex-shrink: 0; }
.domain-info { flex: 1; min-width: 0; }
.domain-name { font-size: 14px; font-weight: 600; color: var(--color-text-primary); }
.domain-key { font-size: 11px; color: var(--color-text-muted); font-family: var(--font-mono); }
.domain-stats { display: flex; align-items: center; gap: 0; background: var(--color-bg-primary); border-radius: var(--radius-md); padding: 10px 0; }
.dstat { flex: 1; text-align: center; }
.dstat-val { display: block; font-size: 18px; font-weight: 700; color: var(--color-accent); font-family: var(--font-mono); }
.dstat-lbl { font-size: 10px; color: var(--color-text-muted); text-transform: uppercase; }
.dstat-divider { width: 1px; height: 28px; background: var(--color-border); }
.domain-card-footer { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-accent); }

/* ── Detail View ── */
.detail-header-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--color-border); }
.detail-header-bar h2 { font-size: 20px; font-weight: 700; color: var(--color-text-primary); flex: 1; }
.detail-panels { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.detail-col { display: flex; flex-direction: column; gap: 12px; }
.col-title { font-size: 15px; font-weight: 600; color: var(--color-text-primary); display: flex; align-items: center; gap: 8px; padding-bottom: 8px; border-bottom: 1px solid var(--color-border); }
.col-empty { padding: 32px; text-align: center; color: var(--color-text-muted); }

/* ── Agent Items ── */
.agent-item { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 14px; cursor: pointer; transition: all var(--transition-fast); }
.agent-item:hover, .agent-item.highlighted { border-color: var(--color-accent); box-shadow: 0 0 0 1px rgba(88,166,255,0.3); }
.agent-item-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
.agent-item-name { font-size: 14px; font-weight: 600; color: var(--color-text-primary); font-family: var(--font-mono); font-size: 12px; }
.agent-item-author { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--color-text-muted); margin-bottom: 4px; }
.agent-item-desc { font-size: 12px; color: var(--color-text-secondary); line-height: 1.4; margin-bottom: 8px; }
.agent-skill-links { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; margin-bottom: 10px; }
.link-label { font-size: 11px; color: var(--color-text-muted); }
.skill-link-tag { cursor: pointer; }
.agent-item-actions { padding-top: 8px; border-top: 1px solid var(--color-border); display: flex; align-items: center; gap: 8px; }
.skill-status-tag { flex-shrink: 0; }
.skill-download-btn { font-size: 11px; padding: 0 6px; }

/* ── Skill Items ── */
.skill-item { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px 14px; transition: all var(--transition-fast); }
.skill-item.linked-by-agent { border-color: var(--color-accent); background: rgba(88,166,255,0.06); }
.skill-item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.skill-item-name { font-size: 12px; font-weight: 600; color: var(--color-success); font-family: var(--font-mono); }
.skill-item-desc { font-size: 11px; color: var(--color-text-secondary); line-height: 1.4; margin-bottom: 6px; }
.skill-agent-links { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }
.agent-link-tag { cursor: pointer; }

/* ── Workflow Items ── */
.workflow-item { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px 14px; }
.workflow-item-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
.workflow-item-name { font-size: 12px; font-weight: 600; color: var(--color-warning); font-family: var(--font-mono); }
.workflow-item-desc { font-size: 11px; color: var(--color-text-secondary); line-height: 1.4; margin-bottom: 6px; }
.workflow-agent-link { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.wf-status { margin-top: 4px; }

/* ── Detail Dialog ── */
.detail-section { margin-bottom: 20px; }
.detail-section h4 { font-size: 13px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 8px; }
.detail-section p { font-size: 13px; color: var(--color-text-secondary); line-height: 1.5; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
</style>
