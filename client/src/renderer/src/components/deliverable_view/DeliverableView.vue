<template>
  <div class="deliverable-view">
    <div class="deliverable-header">
      <span class="deliverable-title">Deliverables</span>
      <span v-if="files.length > 0" class="deliverable-count">{{ files.length }}</span>
    </div>

    <!-- Tabs for multiple files -->
    <div v-if="files.length > 0" class="deliverable-tabs">
      <div
        v-for="file in files"
        :key="file.path || file.name"
        class="deliverable-tab"
        :class="{ active: activeFile === file }"
        @click="activeFile = file"
      >
        <el-icon :size="14">
          <Document v-if="isMarkdown(file)" />
          <Tickets v-else />
        </el-icon>
        <span class="truncate">{{ file.name || file.path }}</span>
        <el-icon
          class="tab-close"
          :size="12"
          @click.stop="closeFile(file)"
        >
          <Close />
        </el-icon>
      </div>
    </div>

    <!-- Content Area -->
    <div class="deliverable-content" v-if="activeFile">
      <!-- Markdown preview -->
      <div
        v-if="isMarkdown(activeFile)"
        class="markdown-preview"
        v-html="renderedMarkdown"
      ></div>

      <!-- Code view -->
      <div v-else class="code-view" ref="codeViewRef"></div>
    </div>

    <!-- Empty -->
    <div v-else class="deliverable-empty">
      <el-icon :size="32"><Folder /></el-icon>
      <p>No deliverables yet</p>
      <span>Generated files will appear here</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Document, Tickets, Close, Folder } from '@element-plus/icons-vue'

const props = defineProps({
  files: {
    type: Array,
    default: () => []
  }
})

const activeFile = ref(null)
const codeViewRef = ref(null)
const renderedMarkdown = ref('')

// Simple markdown detection
function isMarkdown(file) {
  const name = (file.name || file.path || '').toLowerCase()
  return name.endsWith('.md') || name.endsWith('.markdown')
}

async function loadFileContent(file) {
  if (!file.content && file.path) {
    try {
      const result = await window.autodev.readFile(file.path)
      if (result.success) {
        file.content = result.data?.content || result.data || ''
      }
    } catch {
      file.content = '-- Unable to load file --'
    }
  }
}

// Watch active file for content loading and rendering
watch(activeFile, async (file) => {
  if (!file) {
    renderedMarkdown.value = ''
    return
  }

  await loadFileContent(file)
  const content = file.content || ''

  if (isMarkdown(file)) {
    // Simple markdown rendering (markdown-it available globally or inline)
    renderedMarkdown.value = renderMarkdown(content)
  } else {
    // Code view: render after next tick
    await nextTick()
    renderCodeView(content, file)
  }
})

function renderMarkdown(content) {
  // Basic markdown-like rendering
  // In production, use markdown-it or cherry-markdown
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g,
    '<pre class="code-block"><code class="language-$1">$2</code></pre>')
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // Links
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
  // Lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
  // Paragraphs
  html = html.replace(/\n\n/g, '</p><p>')
  html = '<p>' + html + '</p>'

  return html
}

function renderCodeView(content, file) {
  if (!codeViewRef.value) return

  const lang = getLanguage(file)
  // Simple syntax-highlighted pre
  const escaped = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  codeViewRef.value.innerHTML = `<pre class="code-block" data-lang="${lang}"><code>${escaped}</code></pre>`
}

function getLanguage(file) {
  const name = (file.name || file.path || '').toLowerCase()
  if (name.endsWith('.py')) return 'python'
  if (name.endsWith('.js') || name.endsWith('.mjs')) return 'javascript'
  if (name.endsWith('.ts')) return 'typescript'
  if (name.endsWith('.json')) return 'json'
  if (name.endsWith('.yaml') || name.endsWith('.yml')) return 'yaml'
  if (name.endsWith('.html')) return 'html'
  if (name.endsWith('.css') || name.endsWith('.scss')) return 'css'
  if (name.endsWith('.vue')) return 'vue'
  if (name.endsWith('.md')) return 'markdown'
  return 'text'
}

function closeFile(file) {
  if (activeFile.value === file) {
    activeFile.value = props.files.find((f) => f !== file) || null
  }
}
</script>

<style scoped>
.deliverable-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-primary);
  border-left: 1px solid var(--color-border);
}

.deliverable-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.deliverable-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.deliverable-count {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--color-bg-tertiary);
  border-radius: 10px;
  color: var(--color-text-muted);
}

.deliverable-tabs {
  display: flex;
  overflow-x: auto;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  background: var(--color-bg-secondary);
}

.deliverable-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-fast);
  white-space: nowrap;
  flex-shrink: 0;
  max-width: 200px;
}

.deliverable-tab:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-hover);
}

.deliverable-tab.active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

.tab-close {
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.deliverable-tab:hover .tab-close {
  opacity: 0.6;
}

.tab-close:hover {
  opacity: 1 !important;
  color: var(--color-error);
}

.deliverable-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.markdown-preview {
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary);
}

.markdown-preview h1,
.markdown-preview h2,
.markdown-preview h3 {
  color: var(--color-text-primary);
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: 600;
}

.markdown-preview h1 { font-size: 20px; border-bottom: 1px solid var(--color-border); padding-bottom: 8px; }
.markdown-preview h2 { font-size: 17px; }
.markdown-preview h3 { font-size: 15px; }

.markdown-preview p {
  margin-bottom: 12px;
}

.markdown-preview ul {
  padding-left: 20px;
  margin-bottom: 12px;
}

.markdown-preview li {
  margin-bottom: 4px;
}

.code-view {
  font-family: var(--font-mono);
  font-size: 13px;
}

.code-block {
  background: #0a0e14;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
}

.inline-code {
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 0.9em;
  color: var(--color-accent);
}

.deliverable-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: var(--color-text-muted);
}

.deliverable-empty p {
  font-size: 14px;
  font-weight: 500;
}

.deliverable-empty span {
  font-size: 12px;
}
</style>
