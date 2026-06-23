<template>
  <div class="command-bar" :class="{ collapsed: collapsed }">
    <div class="command-bar-header" @click="collapsed = !collapsed">
      <div class="command-bar-title">
        <el-icon><Promotion /></el-icon>
        <span>Quick Command</span>
      </div>
      <el-icon class="collapse-icon" :class="{ rotated: !collapsed }">
        <ArrowDown />
      </el-icon>
    </div>
    <div v-show="!collapsed" class="command-bar-body">
      <div class="command-input-row">
        <el-input
          v-model="instruction"
          placeholder="Describe what you want to build... (e.g., 'Create a REST API for user authentication')"
          size="large"
          :disabled="analyzing"
          @keydown.enter="handleAnalyze"
        >
          <template #prefix>
            <el-icon><ChatLineSquare /></el-icon>
          </template>
          <template #append>
            <el-button
              :loading="analyzing"
              :disabled="!instruction.trim()"
              @click="handleAnalyze"
              type="primary"
            >
              Analyze
            </el-button>
          </template>
        </el-input>
      </div>
      <div class="command-extra">
        <FileUploader @files-selected="handleFiles" />
      </div>
      <div v-if="routingResults.length > 0" class="routing-results">
        <div class="routing-label">Suggested agents:</div>
        <div class="routing-chips">
          <el-tag
            v-for="suggestion in routingResults"
            :key="suggestion.agent_id || suggestion.name"
            :type="suggestion.confidence > 0.7 ? 'success' : 'info'"
            size="large"
            class="routing-chip"
            @click="$emit('use-suggestion', suggestion)"
          >
            <el-icon><MagicStick /></el-icon>
            {{ suggestion.name || suggestion.agent_name }}
            <span class="confidence">{{ Math.round((suggestion.confidence || 0.5) * 100) }}%</span>
          </el-tag>
        </div>
      </div>
      <div v-if="error" class="routing-error">
        <el-alert :title="error" type="error" show-icon :closable="true" @close="error = ''" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FileUploader from '../file_upload/FileUploader.vue'

const emit = defineEmits(['use-suggestion'])

const collapsed = ref(true)
const instruction = ref('')
const analyzing = ref(false)
const routingResults = ref([])
const error = ref('')
const attachedFiles = ref([])

function _getLLMConfig() {
  try {
    const STORAGE_PREFIX = 'autodev:apikey'
    const MODEL_PREFIX = 'autodev:model'
    const DEFAULT_PROVIDER_KEY = 'autodev:defaultProvider'
    const DEFAULT_MODELS = {
      openai: 'gpt-4o', anthropic: 'claude-sonnet-4-6',
      deepseek: 'deepseek-chat', google: 'gemini-2.5-flash', custom: '',
    }
    const provKey = localStorage.getItem(DEFAULT_PROVIDER_KEY)
    if (!provKey) return null
    const apiKey = localStorage.getItem(`${STORAGE_PREFIX}:${provKey}`)
    if (!apiKey) return null
    const model = localStorage.getItem(`${MODEL_PREFIX}:${provKey}`) || DEFAULT_MODELS[provKey] || ''
    return { provider: provKey, api_key: apiKey, model, base_url: '' }
  } catch { return null }
}

async function handleAnalyze() {
  if (!instruction.value.trim()) return
  analyzing.value = true
  error.value = ''
  routingResults.value = []

  try {
    const llmConfig = _getLLMConfig()
    const result = await window.autodev.analyzeRouting({
      text_instruction: instruction.value.trim(),
      uploaded_files: attachedFiles.value.map((f) => f.path),
      llm_config: llmConfig || { provider: 'openai', api_key: '', model: 'gpt-4o', base_url: '' },
    })
    if (result.success) {
      routingResults.value = result.data?.suggestions || result.data?.routes || []
      // Store knowledge chunks for later use
      if (result.data?.knowledge_chunks) {
        sessionStorage.setItem('autodev:pipeline:knowledge', JSON.stringify(result.data.knowledge_chunks))
      }
    } else {
      error.value = result.error || 'Analysis failed'
    }
  } catch (err) {
    error.value = err.message || 'Analysis failed'
  } finally {
    analyzing.value = false
  }
}

function handleFiles(files) {
  attachedFiles.value = files
}
</script>

<style scoped>
.command-bar {
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.command-bar.collapsed {
  border-bottom: 1px solid var(--color-border);
}

.command-bar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
}

.command-bar-header:hover {
  background: var(--color-bg-hover);
}

.command-bar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.collapse-icon {
  transition: transform var(--transition-fast);
  color: var(--color-text-muted);
}

.collapse-icon.rotated {
  transform: rotate(180deg);
}

.command-bar-body {
  padding: 12px 16px 16px;
}

.command-input-row {
  margin-bottom: 12px;
}

.command-extra {
  margin-bottom: 12px;
}

.routing-results {
  margin-top: 12px;
}

.routing-label {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.routing-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.routing-chip {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.confidence {
  opacity: 0.7;
  font-size: 11px;
}

.routing-error {
  margin-top: 12px;
}
</style>
