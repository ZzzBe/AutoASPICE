<template>
  <div class="app-root" :class="{ 'dark-theme': isDark }">
    <AppLayout />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppLayout from './components/layout/AppLayout.vue'

const isDark = ref(true)
</script>

<style>
/* ── Global Reset & Variables ──────────────────────────────── */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  --color-bg-primary: #0d1117;
  --color-bg-secondary: #161b22;
  --color-bg-tertiary: #21262d;
  --color-bg-hover: #30363d;
  --color-border: #30363d;
  --color-border-light: #484f58;
  --color-text-primary: #e6edf3;
  --color-text-secondary: #8b949e;
  --color-text-muted: #6e7681;
  --color-accent: #58a6ff;
  --color-accent-hover: #79c0ff;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-error: #f85149;
  --color-info: #58a6ff;
  --font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
}

html, body {
  height: 100%;
  overflow: hidden;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100%;
}

.app-root {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--color-bg-hover);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-light);
}

/* Element Plus dark theme overrides */
.dark-theme {
  --el-bg-color: var(--color-bg-primary);
  --el-bg-color-overlay: var(--color-bg-secondary);
  --el-text-color-primary: var(--color-text-primary);
  --el-text-color-regular: var(--color-text-secondary);
  --el-border-color: var(--color-border);
  --el-border-color-light: var(--color-border-light);
  --el-fill-color: var(--color-bg-tertiary);
  --el-fill-color-blank: var(--color-bg-secondary);
  --el-color-primary: var(--color-accent);
}

/* Selection */
::selection {
  background: rgba(88, 166, 255, 0.3);
  color: var(--color-text-primary);
}

/* Utility classes */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mono {
  font-family: var(--font-mono);
}
</style>
