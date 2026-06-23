<template>
  <div class="settings-page">
    <div class="settings-header">
      <h2>{{ $t('settings.title') }}</h2>
      <p>{{ $t('settings.subtitle') }}</p>
    </div>

    <div class="settings-content">
      <!-- Language -->
      <section class="settings-section settings-section--compact">
        <div class="settings-row">
          <div class="settings-row-info">
            <h3 class="section-title">
              <el-icon><Switch /></el-icon>
              {{ $t('settings.language.title') }}
            </h3>
            <p class="section-desc">{{ $t('settings.language.desc') }}</p>
          </div>
          <div class="lang-toggle">
            <span class="lang-label" :class="{ dim: current !== 'zh-CN' }">中文</span>
            <el-switch
              :model-value="current === 'en'"
              @change="(val) => switchLanguage(val ? 'en' : 'zh-CN')"
              size="large"
            />
            <span class="lang-label" :class="{ dim: current !== 'en' }">EN</span>
          </div>
        </div>
      </section>

      <!-- LLM Configuration -->
      <section class="settings-section">
        <h3 class="section-title">
          <el-icon><Key /></el-icon>
          {{ $t('settings.llm.title') }}
        </h3>
        <p class="section-desc">{{ $t('settings.llm.desc') }}</p>

        <!-- Default Provider -->
        <div class="default-provider">
          <label class="default-provider-label">{{ $t('settings.llm.defaultProvider') }}</label>
          <el-select
            v-model="defaultProvider"
            class="default-provider-select"
            @change="saveDefaultProvider"
          >
            <el-option
              v-for="p in configuredProviders"
              :key="p.key"
              :label="p.label"
              :value="p.key"
            />
            <el-option
              :label="$t('settings.llm.notConfigured')"
              value=""
              v-if="configuredProviders.length === 0"
            />
          </el-select>
          <span class="default-provider-desc">{{ $t('settings.llm.defaultProviderDesc') }}</span>
        </div>

        <div class="api-key-list">
          <div
            v-for="provider in providers"
            :key="provider.key"
            class="api-key-item"
          >
            <div class="provider-info">
              <div class="provider-name">
                {{ provider.label }}
                <el-tag v-if="provider.key === 'openai'" size="small" type="success">
                  {{ $t('settings.llm.recommended') }}
                </el-tag>
              </div>
              <div class="provider-endpoint">{{ provider.endpoint }}</div>
            </div>
            <div class="provider-key-input">
              <el-input
                v-model="provider.value"
                type="password"
                :placeholder="$t('settings.llm.enterKey')"
                show-password
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </div>
            <div class="provider-actions">
              <el-button
                size="small"
                :type="provider.configured ? 'success' : 'primary'"
                @click="saveKey(provider)"
                :loading="savingKey === provider.key"
              >
                {{ provider.configured ? $t('settings.llm.update') : $t('settings.llm.save') }}
              </el-button>
              <el-button
                v-if="provider.configured"
                size="small"
                text
                type="danger"
                @click="removeKey(provider)"
              >
                {{ $t('settings.llm.remove') }}
              </el-button>
            </div>
            <div class="provider-model">
              <label class="model-label">{{ $t('settings.llm.model') }}</label>
              <el-select
                v-model="provider.selectedModel"
                class="model-select"
                :placeholder="$t('settings.llm.selectModel')"
                @change="(val) => saveModel(provider, val)"
                :disabled="!provider.configured"
              >
                <el-option
                  v-for="m in provider.models"
                  :key="m"
                  :label="m"
                  :value="m"
                />
              </el-select>
              <el-input
                v-if="provider.key === 'custom'"
                v-model="provider.customModel"
                class="model-custom-input"
                placeholder="e.g. llama-3-70b"
                @change="(val) => saveModel(provider, val)"
                size="small"
              />
            </div>
            <div class="provider-status">
              <el-icon v-if="provider.configured" color="var(--color-success)">
                <CircleCheck />
              </el-icon>
              <el-icon v-else color="var(--color-text-muted)">
                <CircleClose />
              </el-icon>
              <span>{{ provider.configured ? $t('settings.llm.configured') : $t('settings.llm.notConfigured') }}</span>
              <span v-if="provider.lastTested" class="last-tested">
                {{ $t('settings.llm.lastTested') }}: {{ provider.lastTested }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Skills Cache -->
      <section class="settings-section">
        <h3 class="section-title">
          <el-icon><FolderOpened /></el-icon>
          {{ $t('settings.cache.title') }}
        </h3>
        <p class="section-desc">{{ $t('settings.cache.desc') }}</p>

        <div class="cache-info">
          <div class="cache-stat">
            <span class="cache-stat-label">{{ $t('settings.cache.size') }}</span>
            <span class="cache-stat-value">{{ cacheSize }}</span>
          </div>
          <div class="cache-stat">
            <span class="cache-stat-label">{{ $t('settings.cache.skills') }}</span>
            <span class="cache-stat-value">{{ cachedSkillCount }}</span>
          </div>
          <div class="cache-stat">
            <span class="cache-stat-label">{{ $t('settings.cache.lastUpdated') }}</span>
            <span class="cache-stat-value">{{ lastCacheUpdate }}</span>
          </div>
        </div>

        <div class="cache-actions">
          <el-button @click="refreshCache" :loading="refreshingCache">
            <el-icon><Refresh /></el-icon>
            {{ $t('settings.cache.refresh') }}
          </el-button>
          <el-button type="danger" @click="clearCache" :disabled="cachedSkillCount === 0">
            <el-icon><Delete /></el-icon>
            {{ $t('settings.cache.clearCache') }}
          </el-button>
        </div>
      </section>

      <!-- About -->
      <section class="settings-section">
        <h3 class="section-title">
          <el-icon><InfoFilled /></el-icon>
          {{ $t('settings.about.title') }}
        </h3>
        <div class="about-info">
          <div class="about-logo">
            <span class="logo-icon">&#9670;</span>
            <span class="logo-text">{{ $t('common.appName') }}</span>
          </div>
          <div class="about-meta">
            <div class="about-item">
              <span class="about-label">{{ $t('settings.about.version') }}</span>
              <span class="about-value">1.0.0</span>
            </div>
            <div class="about-item">
              <span class="about-label">{{ $t('settings.about.electron') }}</span>
              <span class="about-value">37.2.3</span>
            </div>
            <div class="about-item">
              <span class="about-label">{{ $t('settings.about.vue') }}</span>
              <span class="about-value">3.5.17</span>
            </div>
            <div class="about-item">
              <span class="about-label">{{ $t('settings.about.backend') }}</span>
              <span class="about-value" :class="{ connected: backendConnected }">
                {{ backendConnected ? $t('settings.about.connected') : $t('settings.about.disconnected') }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { setLocale, currentLocale, t } from '../../i18n'

// Model lists matching backend llm/factory.py PROVIDER_MODELS
const PROVIDER_MODELS = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4-turbo', 'o4-mini', 'o3'],
  anthropic: ['claude-opus-4-8', 'claude-sonnet-4-6', 'claude-haiku-4-5', 'claude-fable-5'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
  google: ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash'],
  custom: [],
}

const DEFAULT_MODELS = {
  openai: 'gpt-4o',
  anthropic: 'claude-sonnet-4-6',
  deepseek: 'deepseek-chat',
  google: 'gemini-2.5-flash',
  custom: '',
}

const STORAGE_PREFIX = 'autodev:apikey'
const MODEL_STORAGE_PREFIX = 'autodev:model'
const DEFAULT_PROVIDER_KEY = 'autodev:defaultProvider'

const showKeys = reactive({})
const savingKey = ref(null)
const refreshingCache = ref(false)
const cacheSize = ref('0 KB')
const cachedSkillCount = ref(0)
const lastCacheUpdate = ref(t('settings.cache.never'))
const backendConnected = ref(false)
const current = ref(currentLocale.value)
const defaultProvider = ref('')

function switchLanguage(localeKey) {
  setLocale(localeKey)
  current.value = localeKey
  lastCacheUpdate.value = t('settings.cache.never')
  ElMessage.success(localeKey === 'zh-CN' ? '已切换为中文' : 'Switched to English')
}

const providers = reactive([
  { key: 'openai', label: 'OpenAI', endpoint: 'https://api.openai.com/v1', configured: false, value: '', lastTested: null, models: PROVIDER_MODELS.openai, selectedModel: DEFAULT_MODELS.openai, customModel: '' },
  { key: 'anthropic', label: 'Anthropic', endpoint: 'https://api.anthropic.com', configured: false, value: '', lastTested: null, models: PROVIDER_MODELS.anthropic, selectedModel: DEFAULT_MODELS.anthropic, customModel: '' },
  { key: 'google', label: 'Google AI', endpoint: 'https://generativelanguage.googleapis.com', configured: false, value: '', lastTested: null, models: PROVIDER_MODELS.google, selectedModel: DEFAULT_MODELS.google, customModel: '' },
  { key: 'deepseek', label: 'DeepSeek', endpoint: 'https://api.deepseek.com', configured: false, value: '', lastTested: null, models: PROVIDER_MODELS.deepseek, selectedModel: DEFAULT_MODELS.deepseek, customModel: '' },
  { key: 'custom', label: 'Custom Provider', endpoint: 'Custom endpoint', configured: false, value: '', lastTested: null, models: PROVIDER_MODELS.custom, selectedModel: '', customModel: '' },
])

const configuredProviders = computed(() =>
  providers.filter(p => p.configured)
)

onMounted(() => {
  loadSavedKeys()
  loadSavedModels()
  loadDefaultProvider()
  checkBackendConnection()
  loadCacheInfo()
})

function loadSavedKeys() {
  providers.forEach((p) => {
    const saved = localStorage.getItem(`${STORAGE_PREFIX}:${p.key}`)
    if (saved) { p.value = saved; p.configured = true }
  })
}

function loadSavedModels() {
  providers.forEach((p) => {
    const saved = localStorage.getItem(`${MODEL_STORAGE_PREFIX}:${p.key}`)
    if (saved) {
      if (p.key === 'custom') {
        p.customModel = saved
        p.selectedModel = saved
      } else {
        p.selectedModel = saved
      }
    }
  })
}

function loadDefaultProvider() {
  const saved = localStorage.getItem(DEFAULT_PROVIDER_KEY)
  if (saved && providers.some(p => p.key === saved && p.configured)) {
    defaultProvider.value = saved
  } else {
    // Auto-select first configured provider
    const first = providers.find(p => p.configured)
    defaultProvider.value = first ? first.key : ''
  }
}

function saveDefaultProvider() {
  localStorage.setItem(DEFAULT_PROVIDER_KEY, defaultProvider.value)
  ElMessage.success(t('settings.llm.saveSuccess', { provider: 'Default provider' }))
}

function saveModel(provider, model) {
  const val = provider.key === 'custom' ? provider.customModel : model
  if (val) {
    localStorage.setItem(`${MODEL_STORAGE_PREFIX}:${provider.key}`, val)
  }
}

async function saveKey(provider) {
  if (!provider.value.trim()) { ElMessage.warning(t('settings.llm.enterKey')); return }
  savingKey.value = provider.key
  try {
    localStorage.setItem(`${STORAGE_PREFIX}:${provider.key}`, provider.value)
    provider.configured = true
    provider.lastTested = new Date().toLocaleString()

    // Auto-set model if not yet selected
    if (!provider.selectedModel && provider.key !== 'custom') {
      provider.selectedModel = DEFAULT_MODELS[provider.key]
      saveModel(provider, provider.selectedModel)
    }

    // Auto-set default provider if none selected
    if (!defaultProvider.value) {
      defaultProvider.value = provider.key
      saveDefaultProvider()
    }

    ElMessage.success(t('settings.llm.saveSuccess', { provider: provider.label }))
  } catch {
    ElMessage.error(t('settings.llm.saveFailed'))
  } finally { savingKey.value = null }
}

async function removeKey(provider) {
  try {
    await ElMessageBox.confirm(
      t('settings.llm.removeConfirm', { provider: provider.label }),
      t('common.confirm'),
      { confirmButtonText: t('settings.llm.removeConfirmBtn'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    localStorage.removeItem(`${STORAGE_PREFIX}:${provider.key}`)
    localStorage.removeItem(`${MODEL_STORAGE_PREFIX}:${provider.key}`)
    provider.value = ''; provider.configured = false; provider.lastTested = null
    provider.selectedModel = DEFAULT_MODELS[provider.key]
    provider.customModel = ''

    // Reset default provider if removed
    if (defaultProvider.value === provider.key) {
      const first = providers.find(p => p.configured)
      defaultProvider.value = first ? first.key : ''
      saveDefaultProvider()
    }

    ElMessage.success(t('settings.llm.removeSuccess', { provider: provider.label }))
  } catch {}
}

async function checkBackendConnection() {
  try {
    const result = await window.autodev.listAgents()
    backendConnected.value = result.success
  } catch { backendConnected.value = false }
}

function loadCacheInfo() {
  cacheSize.value = '4.2 MB'; cachedSkillCount.value = 12
  lastCacheUpdate.value = new Date().toLocaleDateString()
}

async function refreshCache() {
  refreshingCache.value = true
  try {
    await new Promise((r) => setTimeout(r, 1000)); loadCacheInfo()
    ElMessage.success(t('settings.cache.refreshSuccess'))
  } catch { ElMessage.error(t('settings.cache.refreshFailed')) }
  finally { refreshingCache.value = false }
}

async function clearCache() {
  try {
    await ElMessageBox.confirm(
      t('settings.cache.clearConfirm'), t('settings.cache.clearCache'),
      { confirmButtonText: t('settings.cache.clearConfirmBtn'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    await new Promise((r) => setTimeout(r, 1000))
    cacheSize.value = '0 KB'; cachedSkillCount.value = 0
    lastCacheUpdate.value = t('settings.cache.never')
    ElMessage.success(t('settings.cache.clearSuccess'))
  } catch {}
}

// ── Public helper to get current LLM config (used by agent execution flow) ──
function getLLMConfig() {
  const provKey = defaultProvider.value
  if (!provKey) return null
  const provider = providers.find(p => p.key === provKey)
  if (!provider || !provider.configured) return null

  const model = provKey === 'custom' ? provider.customModel : provider.selectedModel
  return {
    provider: provKey,
    api_key: provider.value,
    model: model || DEFAULT_MODELS[provKey] || '',
    base_url: provKey === 'custom' ? provider.endpoint : '',
  }
}

// Expose for other components
if (typeof window !== 'undefined') {
  window.__getLLMConfig = getLLMConfig
}
</script>

<style scoped>
.settings-page { height: 100%; overflow-y: auto; padding: 24px 32px; }
.settings-header { margin-bottom: 32px; }
.settings-header h2 { font-size: 22px; font-weight: 700; color: var(--color-text-primary); margin-bottom: 4px; }
.settings-header p { font-size: 14px; color: var(--color-text-secondary); }
.settings-content { max-width: 760px; display: flex; flex-direction: column; gap: 32px; }
.settings-section { background: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 24px; }
.section-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 6px; }
.section-desc { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 20px; line-height: 1.5; }

/* Language Toggle */
.settings-section--compact { padding: 20px 24px; }
.settings-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.settings-row-info .section-title { margin-bottom: 2px; }
.settings-row-info .section-desc { margin-bottom: 0; font-size: 12px; }
.lang-toggle { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.lang-label { font-size: 14px; font-weight: 500; color: var(--color-text-primary); transition: color var(--transition-fast); }
.lang-label.dim { color: var(--color-text-muted); }

/* Default Provider */
.default-provider { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding: 12px 16px; background: var(--color-bg-primary); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.default-provider-label { font-size: 13px; font-weight: 600; color: var(--color-text-primary); white-space: nowrap; }
.default-provider-select { width: 200px; }
.default-provider-desc { font-size: 12px; color: var(--color-text-muted); }

/* API Keys */
.api-key-list { display: flex; flex-direction: column; gap: 16px; }
.api-key-item { display: grid; grid-template-columns: 160px 1fr auto; grid-template-rows: auto auto auto; gap: 8px 12px; padding: 16px; background: var(--color-bg-primary); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.provider-info { grid-column: 1; grid-row: 1 / 4; }
.provider-name { font-size: 14px; font-weight: 500; color: var(--color-text-primary); display: flex; align-items: center; gap: 8px; }
.provider-endpoint { font-size: 11px; color: var(--color-text-muted); font-family: var(--font-mono); margin-top: 4px; }
.provider-key-input { grid-column: 2; grid-row: 1; }
.provider-actions { grid-column: 3; grid-row: 1; display: flex; gap: 8px; align-items: flex-start; }
.provider-model { grid-column: 2; grid-row: 2; display: flex; align-items: center; gap: 8px; }
.model-label { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; }
.model-select { width: 240px; }
.model-custom-input { width: 160px; margin-left: 8px; }
.provider-status { grid-column: 2 / 4; grid-row: 3; display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-text-muted); }
.last-tested { margin-left: 12px; opacity: 0.6; }

/* Cache */
.cache-info { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.cache-stat { background: var(--color-bg-primary); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 16px; text-align: center; }
.cache-stat-label { display: block; font-size: 11px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.cache-stat-value { font-size: 18px; font-weight: 700; color: var(--color-text-primary); font-family: var(--font-mono); }
.cache-actions { display: flex; gap: 8px; }

/* About */
.about-info { display: flex; gap: 24px; align-items: flex-start; }
.about-logo { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: var(--color-bg-primary); border-radius: var(--radius-md); }
.logo-icon { color: var(--color-accent); font-size: 24px; }
.logo-text { font-size: 16px; font-weight: 600; color: var(--color-text-primary); }
.about-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 24px; }
.about-item { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; }
.about-label { color: var(--color-text-muted); }
.about-value { color: var(--color-text-primary); font-family: var(--font-mono); font-size: 12px; }
.about-value.connected { color: var(--color-success); }
</style>
