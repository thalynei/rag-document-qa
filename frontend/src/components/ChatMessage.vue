<script setup lang="ts">
import { computed } from 'vue'
import { Bot, Copy, RefreshCw, Quote, ChevronDown, User } from 'lucide-vue-next'
import type { Message } from '../types'
import SourceCard from './SourceCard.vue'
import { useMarkdown } from '../composables/useMarkdown'
import { useChatStore } from '../stores/chat'
import { useToastStore } from '../stores/toast'

const props = defineProps<{
  message: Message
  index: number
}>()

const store = useChatStore()
const md = useMarkdown()
const toast = useToastStore()

const renderedContent = computed(() => {
  if (props.message.role === 'user') return props.message.content
  return md.render(props.message.content)
})

const timeStr = computed(() => {
  return new Date(props.message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})

function copyMessage() {
  navigator.clipboard.writeText(props.message.content)
  toast.show('已复制到剪贴板', 'success')
}

function regenerate() {
  store.regenerateMessage(props.index)
}
</script>

<template>
  <div class="message-row" :class="message.role">
    <!-- User Message -->
    <template v-if="message.role === 'user'">
      <div class="user-bubble">
        <p>{{ message.content }}</p>
      </div>
      <div class="avatar user-avatar">
        <User :size="18" />
      </div>
    </template>

    <!-- Assistant Message -->
    <template v-else>
      <div class="avatar ai-avatar">
        <Bot :size="18" />
      </div>
      <div class="ai-content">
        <div class="ai-header">
          <span class="ai-name">AI 助手</span>
          <span class="ai-time">{{ timeStr }}</span>
        </div>

        <div class="ai-bubble">
          <div
            v-if="message.content"
            class="prose"
            v-html="renderedContent"
          />
          <span v-if="message.isStreaming && !message.content" class="thinking">
            <span class="dot" />
            <span class="dot" />
            <span class="dot" />
          </span>
          <span v-if="message.isStreaming && message.content" class="streaming-cursor" />
        </div>

        <!-- Actions -->
        <div v-if="!message.isStreaming && message.content" class="actions">
          <button @click="copyMessage" class="action-btn">
            <Copy :size="14" />
            <span>复制</span>
          </button>
          <button @click="regenerate" class="action-btn">
            <RefreshCw :size="14" />
            <span>重新生成</span>
          </button>
        </div>

        <!-- Sources -->
        <template v-if="message.sources && message.sources.length > 0 && !message.isStreaming">
          <details class="sources">
            <summary class="sources-toggle">
              <Quote :size="14" />
              {{ message.sources.length }} 条引用来源
              <ChevronDown :size="14" />
            </summary>
            <div class="sources-list">
              <SourceCard
                v-for="(src, i) in message.sources"
                :key="i"
                :source="src.source"
                :content="src.content"
              />
            </div>
          </details>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
.message-row {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  animation: fade-in-up 0.3s ease-out;
}

.message-row.user {
  flex-direction: row-reverse;
}

/* Avatars */
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.user-avatar {
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.ai-avatar {
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  color: white;
  box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
}

/* User Bubble */
.user-bubble {
  max-width: 75%;
  padding: 0.875rem 1.25rem;
  background: var(--color-surface);
  border-radius: 18px 18px 4px 18px;
  transition: background 0.2s;
}

.user-bubble:hover {
  background: var(--color-surface-hover);
}

.user-bubble p {
  font-size: 0.95rem;
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--color-text);
}

/* AI Content */
.ai-content {
  flex: 1;
  min-width: 0;
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.ai-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text);
}

.ai-time {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.ai-bubble {
  padding: 1rem 1.25rem;
  background: var(--color-surface);
  border-radius: 4px 18px 18px 18px;
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--color-text);
}

/* Thinking dots */
.thinking {
  display: flex;
  gap: 4px;
  padding: 0.25rem 0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: dot-pulse 1.4s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* Actions */
.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-row:hover .actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 8px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

/* Sources */
.sources {
  margin-top: 0.75rem;
}

.sources-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-primary-light);
  background: var(--color-primary-subtle);
  cursor: pointer;
  transition: all 0.2s;
  list-style: none;
}

.sources-toggle::-webkit-details-marker {
  display: none;
}

.sources-toggle:hover {
  background: var(--color-primary);
  color: white;
}

.sources-list {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
