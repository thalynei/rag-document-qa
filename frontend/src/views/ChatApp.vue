<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Menu, MessageSquare } from 'lucide-vue-next'
import { useChatStore } from '../stores/chat'
import { useThemeStore } from '../stores/theme'
import { useConversationStore } from '../stores/conversation'
import { useAuthStore } from '../stores/auth'
import Sidebar from '../components/Sidebar.vue'
import ChatView from '../components/ChatView.vue'
import ToastNotification from '../components/ToastNotification.vue'

const chatStore = useChatStore()
const themeStore = useThemeStore()
const convStore = useConversationStore()
const authStore = useAuthStore()
const sidebarOpen = ref(false)

onMounted(async () => {
  themeStore.init()
  chatStore.status()
  await convStore.fetchConversations()

  // 自动选择第一个对话
  if (convStore.conversations.length > 0 && !convStore.currentConversation) {
    try {
      const conv = await convStore.selectConversation(convStore.conversations[0].id)
      if (conv.messages) {
        chatStore.clearMessages()
        for (const msg of conv.messages) {
          chatStore.messages.push({
            id: msg.id.toString(),
            role: msg.role,
            content: msg.content,
            sources: msg.sources,
            timestamp: new Date(msg.created_at).getTime(),
          })
        }
      }
    } catch (e) {
      console.error('加载对话失败:', e)
    }
  }
})
</script>

<template>
  <div class="flex h-full bg-[var(--color-bg)]">
    <!-- Desktop Sidebar -->
    <Sidebar
      class="hidden md:flex"
      @close="sidebarOpen = false"
    />

    <!-- Mobile Sidebar Overlay -->
    <Transition name="sidebar">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-50 md:hidden"
      >
        <div
          class="absolute inset-0 bg-black/50"
          @click="sidebarOpen = false"
        />
        <div class="absolute inset-y-0 left-0 w-[var(--sidebar-width)]">
          <Sidebar @close="sidebarOpen = false" />
        </div>
      </div>
    </Transition>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top Bar (mobile) -->
      <div class="md:hidden flex items-center gap-3 px-4 py-3 border-b border-[var(--color-border)]">
        <button
          @click="sidebarOpen = !sidebarOpen"
          class="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
        >
          <Menu :size="20" class="text-[var(--color-text-secondary)]" />
        </button>
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-[#6C63FF] to-[#FF6B9D] flex items-center justify-center">
            <MessageSquare :size="14" class="text-white" />
          </div>
          <span class="font-semibold text-[var(--color-text)]">RAG QA</span>
        </div>
      </div>

      <!-- Chat Area -->
      <ChatView />
    </div>

    <!-- Toast -->
    <ToastNotification />
  </div>
</template>
