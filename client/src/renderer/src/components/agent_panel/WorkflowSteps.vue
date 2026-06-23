<template>
  <div class="workflow-steps">
    <div class="workflow-header">
      <span class="workflow-title">Workflow</span>
      <span class="workflow-progress">
        {{ completedSteps }} / {{ steps.length }} steps
      </span>
    </div>
    <div class="steps-list">
      <div
        v-for="(step, index) in steps"
        :key="step.id || index"
        class="step-item"
        :class="{
          'step--pending': step.status === 'pending',
          'step--running': step.status === 'running',
          'step--completed': step.status === 'completed',
          'step--paused': step.status === 'paused',
          'step--failed': step.status === 'failed',
          'step--active': index === currentStepIndex
        }"
      >
        <div class="step-indicator">
          <div class="step-circle">
            <el-icon v-if="step.status === 'completed'" class="step-check">
              <Check />
            </el-icon>
            <el-icon v-else-if="step.status === 'running'" class="step-spin is-loading">
              <Loading />
            </el-icon>
            <el-icon v-else-if="step.status === 'failed'">
              <Close />
            </el-icon>
            <span v-else class="step-number">{{ index + 1 }}</span>
          </div>
          <div v-if="index < steps.length - 1" class="step-line" :class="{
            'step-line--done': step.status === 'completed'
          }"></div>
        </div>
        <div class="step-content">
          <div class="step-name">
            {{ step.name || `Step ${index + 1}` }}
            <el-tag
              v-if="step.is_checkpoint"
              size="small"
              type="warning"
              class="checkpoint-tag"
            >
              Checkpoint
            </el-tag>
          </div>
          <div v-if="step.description" class="step-description">
            {{ step.description }}
          </div>
          <div v-if="step.status === 'running' && step.progress !== undefined" class="step-progress">
            <el-progress
              :percentage="Math.round((step.progress || 0) * 100)"
              :stroke-width="4"
              :show-text="false"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check, Close, Loading } from '@element-plus/icons-vue'

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  }
})

const completedSteps = computed(() =>
  props.steps.filter((s) => s.status === 'completed').length
)

const currentStepIndex = computed(() =>
  props.steps.findIndex(
    (s) => s.status === 'running' || s.status === 'paused'
  )
)
</script>

<style scoped>
.workflow-steps {
  padding: 12px;
}

.workflow-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.workflow-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.workflow-progress {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.steps-list {
  display: flex;
  flex-direction: column;
}

.step-item {
  display: flex;
  gap: 12px;
  padding: 4px 0;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 28px;
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--color-border);
  background: var(--color-bg-secondary);
  font-size: 12px;
  font-weight: 600;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.step-number {
  color: var(--color-text-muted);
}

.step--running .step-circle {
  border-color: var(--color-accent);
  background: rgba(88, 166, 255, 0.1);
}

.step--completed .step-circle {
  border-color: var(--color-success);
  background: rgba(63, 185, 80, 0.1);
}

.step-check {
  color: var(--color-success);
}

.step-spin {
  color: var(--color-accent);
}

.step--failed .step-circle {
  border-color: var(--color-error);
  background: rgba(248, 81, 73, 0.1);
  color: var(--color-error);
}

.step--paused .step-circle {
  border-color: var(--color-warning);
  background: rgba(210, 153, 34, 0.1);
}

.step-line {
  width: 2px;
  flex: 1;
  min-height: 20px;
  background: var(--color-border);
  margin: 4px 0;
}

.step-line--done {
  background: var(--color-success);
}

.step-content {
  flex: 1;
  min-width: 0;
  padding-bottom: 12px;
}

.step-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.step--pending .step-name {
  color: var(--color-text-muted);
}

.step--failed .step-name {
  color: var(--color-error);
}

.checkpoint-tag {
  font-size: 10px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
}

.step-description {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.step-progress {
  margin-top: 6px;
  width: 100%;
}
</style>
