<script setup lang="ts">
import { Sparkles, FileText, MessageSquare, BookOpen, Zap } from 'lucide-vue-next'

const emit = defineEmits<{
  select: [question: string]
}>()

const quickStarts = [
  { icon: FileText, text: '帮我总结这份文档的要点', color: '#6C63FF' },
  { icon: MessageSquare, text: '解释文档中的核心概念', color: '#FF6B9D' },
  { icon: BookOpen, text: '提取文档中的关键数据', color: '#10A37F' },
  { icon: Zap, text: '你是谁？有什么功能？', color: '#F59E0B' },
]
</script>

<template>
  <div class="welcome-container">
    <!-- Logo & Title -->
    <div class="welcome-header">
      <div class="welcome-logo">
        <Sparkles :size="36" class="text-white" />
      </div>
      <h1 class="welcome-title">RAG 智能文档问答</h1>
      <p class="welcome-subtitle">直接开始对话，或上传文档获得更精准的回答</p>
    </div>

    <!-- Quick Start Cards -->
    <div class="quick-start-grid">
      <button
        v-for="(item, i) in quickStarts"
        :key="item.text"
        @click="emit('select', item.text)"
        class="quick-card"
        :style="{ animationDelay: `${0.1 + i * 0.1}s` }"
      >
        <div class="quick-icon" :style="{ background: item.color + '18', color: item.color }">
          <component :is="item.icon" :size="20" />
        </div>
        <span>{{ item.text }}</span>
      </button>
    </div>

    <!-- Hint -->
    <p class="welcome-hint">
      在下方输入问题开始对话 · 支持上传 PDF / DOCX / MD / TXT 文档
    </p>
  </div>
</template>

<style scoped>
.welcome-container {
  max-width: 680px;
  margin: 0 auto;
  padding: 2rem;
  animation: fade-in-up 0.5s ease-out;
}

.welcome-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.welcome-logo {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  box-shadow: 0 8px 30px rgba(108, 99, 255, 0.3);
  animation: float 3s ease-in-out infinite;
}

.welcome-title {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.75rem;
}

.welcome-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  max-width: 400px;
  margin: 0 auto;
  line-height: 1.6;
}

.quick-start-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-bottom: 2rem;
}

@media (max-width: 640px) {
  .quick-start-grid {
    grid-template-columns: 1fr;
  }
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.25s ease;
  text-align: left;
  animation: fade-in-up 0.5s ease-out both;
}

.quick-card:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.quick-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-card span {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.quick-card:hover span {
  color: var(--color-text);
}

.welcome-hint {
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  opacity: 0.6;
}
</style>
