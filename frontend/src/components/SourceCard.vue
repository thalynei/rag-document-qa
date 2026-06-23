<script setup lang="ts">
import { computed } from 'vue'
import { Copy, FileText, Hash } from 'lucide-vue-next'
import { useToastStore } from '../stores/toast'

const props = defineProps<{
  source: string
  content: string
  page?: string
  score?: number | null
  index?: number
}>()

const toast = useToastStore()

const scorePercent = computed(() => {
  if (props.score == null || props.score === 0) return null
  return Math.round(props.score * 100)
})

const scoreColor = computed(() => {
  const s = scorePercent.value ?? 0
  if (s >= 80) return 'var(--color-success)'
  if (s >= 60) return 'var(--color-warning)'
  return 'var(--color-error)'
})

const displaySource = computed(() => {
  let name = props.source
  if (props.page) {
    name += ` · ${props.page}`
  }
  return name
})

function copyContent() {
  navigator.clipboard.writeText(props.content)
  toast.show('已复制引用内容', 'success')
}
</script>

<template>
  <div class="source-card group">
    <div class="source-header">
      <div class="source-labels">
        <span v-if="index != null" class="source-index">[{{ index + 1 }}]</span>
        <span class="source-name">
          <FileText :size="12" />
          {{ displaySource }}
        </span>
      </div>
      <div class="source-actions">
        <span v-if="scorePercent != null" class="score-badge" :style="{ color: scoreColor, background: scoreColor + '15' }">
          <Hash :size="10" />
          {{ scorePercent }}%
        </span>
        <button
          @click="copyContent"
          class="copy-btn opacity-0 group-hover:opacity-100"
          title="复制"
        >
          <Copy :size="12" />
        </button>
      </div>
    </div>

    <!-- Relevance bar -->
    <div v-if="scorePercent != null" class="relevance-bar-wrap">
      <div class="relevance-bar" :style="{ width: scorePercent + '%', background: scoreColor }" />
    </div>

    <p class="source-content">{{ content }}</p>
  </div>
</template>

<style scoped>
.source-card {
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  transition: all 0.2s;
}

.source-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 12px rgba(108, 99, 255, 0.08);
}

.source-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
}

.source-labels {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  min-width: 0;
  flex: 1;
}

.source-index {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--color-primary);
  background: var(--color-primary-subtle);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  flex-shrink: 0;
}

.source-name {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-family: monospace;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-actions {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.125rem;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.copy-btn {
  padding: 0.25rem;
  border-radius: 6px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.relevance-bar-wrap {
  height: 3px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.relevance-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

.source-content {
  font-size: 0.8rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
}
</style>
