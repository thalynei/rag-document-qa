<script setup lang="ts">
import { computed } from 'vue'
import { BarChart3, Target, Quote, TrendingUp } from 'lucide-vue-next'
import type { RAGEvaluation } from '../types'

const props = defineProps<{
  evaluation: RAGEvaluation
}>()

const retrievalScore = computed(() => {
  return Math.round((props.evaluation.retrieval?.context_precision || 0) * 100)
})

const relevanceScore = computed(() => {
  return Math.round((props.evaluation.retrieval?.avg_relevance_score || 0) * 100)
})

const citationScore = computed(() => {
  return Math.round((props.evaluation.citation?.coverage || 0) * 100)
})

function getScoreColor(score: number): string {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  return 'var(--color-error)'
}
</script>

<template>
  <div class="eval-panel">
    <div class="eval-header">
      <BarChart3 :size="14" />
      <span>RAG 质量评估</span>
    </div>

    <div class="eval-metrics">
      <!-- 检索精确度 -->
      <div class="metric-item">
        <div class="metric-icon">
          <Target :size="14" />
        </div>
        <div class="metric-info">
          <span class="metric-label">检索精确度</span>
          <div class="metric-bar-wrap">
            <div class="metric-bar" :style="{ width: retrievalScore + '%', background: getScoreColor(retrievalScore) }" />
          </div>
        </div>
        <span class="metric-value" :style="{ color: getScoreColor(retrievalScore) }">
          {{ retrievalScore }}%
        </span>
      </div>

      <!-- 平均相关度 -->
      <div class="metric-item">
        <div class="metric-icon">
          <TrendingUp :size="14" />
        </div>
        <div class="metric-info">
          <span class="metric-label">平均相关度</span>
          <div class="metric-bar-wrap">
            <div class="metric-bar" :style="{ width: relevanceScore + '%', background: getScoreColor(relevanceScore) }" />
          </div>
        </div>
        <span class="metric-value" :style="{ color: getScoreColor(relevanceScore) }">
          {{ relevanceScore }}%
        </span>
      </div>

      <!-- 引用覆盖率 -->
      <div class="metric-item" v-if="evaluation.citation">
        <div class="metric-icon">
          <Quote :size="14" />
        </div>
        <div class="metric-info">
          <span class="metric-label">引用覆盖率</span>
          <div class="metric-bar-wrap">
            <div class="metric-bar" :style="{ width: citationScore + '%', background: getScoreColor(citationScore) }" />
          </div>
        </div>
        <span class="metric-value" :style="{ color: getScoreColor(citationScore) }">
          {{ citationScore }}%
        </span>
      </div>
    </div>

    <!-- 详细分数 -->
    <div class="eval-detail" v-if="evaluation.retrieval.top_k_scores.length > 0">
      <span class="detail-label">Top-{{ evaluation.retrieval.top_k_scores.length }} 分数:</span>
      <span
        v-for="(score, i) in evaluation.retrieval.top_k_scores"
        :key="i"
        class="score-chip"
        :style="{ background: getScoreColor(Math.round(score * 100)) + '20', color: getScoreColor(Math.round(score * 100)) }"
      >
        {{ Math.round(score * 100) }}%
      </span>
    </div>
  </div>
</template>

<style scoped>
.eval-panel {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  font-size: 0.8rem;
}

.eval-header {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--color-text-muted);
  font-weight: 500;
  margin-bottom: 0.625rem;
}

.eval-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metric-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  flex-shrink: 0;
}

.metric-info {
  flex: 1;
  min-width: 0;
}

.metric-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  display: block;
  margin-bottom: 0.25rem;
}

.metric-bar-wrap {
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.metric-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

.metric-value {
  font-size: 0.8rem;
  font-weight: 600;
  flex-shrink: 0;
  min-width: 36px;
  text-align: right;
}

.eval-detail {
  margin-top: 0.625rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-wrap: wrap;
}

.detail-label {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.score-chip {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}
</style>
