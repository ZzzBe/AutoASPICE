<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-left">
        <div class="app-logo" @click="$router.push('/')">
          <span class="logo-icon">&#9670;</span>
          <span class="logo-text">{{ $t('common.appName') }}</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="nav-item" active-class="nav-item--active">
            <el-icon><Monitor /></el-icon>
            <span>{{ $t('nav.dashboard') }}</span>
          </router-link>
          <router-link to="/agents" class="nav-item" active-class="nav-item--active">
            <el-icon><MagicStick /></el-icon>
            <span>{{ $t('nav.agents') }}</span>
          </router-link>
          <router-link to="/settings" class="nav-item" active-class="nav-item--active">
            <el-icon><Setting /></el-icon>
            <span>{{ $t('nav.settings') }}</span>
          </router-link>
        </nav>
      </div>
      <div class="header-right">
        <div v-if="projectStore.currentProject" class="current-project-badge">
          <el-icon><Folder /></el-icon>
          <span>{{ projectStore.currentProject.name }}</span>
        </div>
      </div>
    </header>
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['DashboardPage', 'AgentMarket', 'SettingsPage']">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useProjectStore } from '../../store/project'
import { useAgentStore } from '../../store/agent'

const projectStore = useProjectStore()
const agentStore = useAgentStore()

onMounted(() => {
  if (window.autodev) {
    projectStore.loadProjects()
    agentStore.loadAgents()
    agentStore.setupWsListener()
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  -webkit-app-region: drag;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
  -webkit-app-region: no-drag;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.logo-icon {
  font-size: 18px;
  color: var(--color-accent);
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.2px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 13px;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-hover);
}

.nav-item--active {
  color: var(--color-accent);
  background: rgba(88, 166, 255, 0.1);
}

.header-right {
  display: flex;
  align-items: center;
  -webkit-app-region: no-drag;
}

.current-project-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: rgba(63, 185, 80, 0.15);
  border: 1px solid rgba(63, 185, 80, 0.3);
  border-radius: var(--radius-lg);
  color: var(--color-success);
  font-size: 12px;
  font-weight: 500;
}

.app-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
