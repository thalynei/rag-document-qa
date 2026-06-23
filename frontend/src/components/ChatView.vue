<script setup lang="ts">
import { ref, nextTick, watch, computed } from 'vue'
import { Eraser, MessageSquare } from 'lucide-vue-next'
import { useChatStore } from '../stores/chat'
import { useConversationStore } from '../stores/conversation'
import { useToastStore } from '../stores/toast'
import { uploadTempFile } from '../services/api'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import EmptyState from './EmptyState.vue'

const store = useChatStore()
const convStore = useConversationStore()
const toast = useToastStore()
const messagesContainer = ref<HTMLDivElement | null>(null)

const showWelcome = computed(() => store.messages.length === 0)

const currentTitle = computed(() => {
  if (convStore.currentConversation) {
    return convStore.currentConversation.title
  }
  return 'AI 助手'
})

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(() => store.messages.length, scrollToBottom)
watch(() => store.messages[store.messages.length - 1]?.content, scrollToBottom)

async function onSend(question: string) {
  await store.sendMessage(question)
}

async function onUpload(file: File) {
  try {
    // 显示上传中的消息
    const uploadingMsg = {
      id: Date.now().toString(),
      role: 'assistant' as const,
      content: `正在解析文档 "${file.name}"，请稍候...`,
      isStreaming: false,
      timestamp: Date.now(),
    }
    store.messages.push(uploadingMsg)

    // 使用临时上传 API（传入当前对话 ID 以隔离临时文件）
    const result = await uploadTempFile(file, convStore.currentConversation?.id)

    // 移除上传中的消息
    const idx = store.messages.findIndex(m => m.id === uploadingMsg.id)
    if (idx !== -1) {
      store.messages.splice(idx, 1)
    }

    // 添加成功消息
    const successMsg = {
      id: Date.now().toString(),
      role: 'assistant' as const,
      content: `文档 "${result.filename}" 已解析完成！现在您可以询问关于这个文档的问题了。\n\n💡 提示：此文档仅在当前会话有效，切换对话后需要重新上传。`,
      isStreaming: false,
      timestamp: Date.now(),
    }
    store.messages.push(successMsg)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '上传失败'
    toast.show(msg, 'error')
  }
}

function onSuggested(q: string) {
  store.sendMessage(q)
}
</script>

<template>
  <div class="chat-view">
    <!-- Header -->
    <header class="chat-header">
      <div class="header-left">
        <div class="header-icon">
          <MessageSquare :size="16" />
        </div>
        <div>
          <h2>{{ currentTitle }}</h2>
          <span v-if="store.documents.length > 0" class="badge">
            {{ store.documents.length }} 个文档
          </span>
          <span v-else class="badge">通用对话模式</span>
        </div>
      </div>

      <button
        v-if="store.messages.length > 0"
        @click="store.clearMessages()"
        class="clear-btn"
      >
        <Eraser :size="15" />
        <span>清空对话</span>
      </button>
    </header>

    <!-- Messages -->
    <main ref="messagesContainer" class="messages-area">
      <!-- Welcome -->
      <div v-if="showWelcome" class="welcome-wrapper">
        <EmptyState @select="onSuggested" />
      </div>

      <!-- Messages -->
      <div v-else class="messages-list">
        <ChatMessage
          v-for="(msg, i) in store.messages"
          :key="msg.id"
          :message="msg"
          :index="i"
        />
      </div>
    </main>

    <!-- Input -->
    <ChatInput
      :disabled="store.isStreaming"
      @send="onSend"
      @upload="onUpload"
    />
  </div>
</template>

<style scoped>
.chat-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--color-bg);
}

/* Header */
.chat-header {
  display: none;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  position: sticky;
  top: 0;
  z-index: 10;
}

@media (min-width: 768px) {
  .chat-header {
    display: flex;
  }
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-left h2 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.header-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.badge {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  background: var(--color-surface);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 10px;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

/* Messages Area */
.messages-area {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.welcome-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.messages-list {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
</style>
