import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count: number
  messages?: Message[]
}

export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  sources?: { source: string; content: string }[]
  created_at: string
}

export const useConversationStore = defineStore('conversation', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const loading = ref(false)

  const sortedConversations = computed(() => {
    return [...conversations.value].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  })

  async function fetchConversations() {
    const auth = useAuthStore()
    if (!auth.isAuthenticated) return

    loading.value = true
    try {
      const res = await fetch('/api/conversations', {
        headers: auth.authHeaders(),
      })
      if (res.ok) {
        conversations.value = await res.json()
      }
    } catch (e) {
      console.error('Failed to fetch conversations:', e)
    } finally {
      loading.value = false
    }
  }

  async function createConversation(title: string = '新对话'): Promise<Conversation> {
    const auth = useAuthStore()
    const res = await fetch('/api/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...auth.authHeaders(),
      },
      body: JSON.stringify({ title }),
    })

    if (!res.ok) throw new Error('创建对话失败')

    const conv = await res.json()
    conversations.value.unshift(conv)
    currentConversation.value = conv
    return conv
  }

  async function selectConversation(convId: number) {
    const auth = useAuthStore()
    const res = await fetch(`/api/conversations/${convId}`, {
      headers: auth.authHeaders(),
    })

    if (!res.ok) throw new Error('获取对话失败')

    const conv = await res.json()
    currentConversation.value = conv
    return conv
  }

  async function deleteConversation(convId: number) {
    const auth = useAuthStore()
    const res = await fetch(`/api/conversations/${convId}`, {
      method: 'DELETE',
      headers: auth.authHeaders(),
    })

    if (!res.ok) throw new Error('删除对话失败')

    conversations.value = conversations.value.filter((c) => c.id !== convId)
    if (currentConversation.value?.id === convId) {
      currentConversation.value = null
    }
  }

  async function updateTitle(convId: number, title: string) {
    const auth = useAuthStore()
    const res = await fetch(`/api/conversations/${convId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...auth.authHeaders(),
      },
      body: JSON.stringify({ title }),
    })

    if (!res.ok) throw new Error('更新标题失败')

    const updated = await res.json()
    const idx = conversations.value.findIndex((c) => c.id === convId)
    if (idx !== -1) {
      conversations.value[idx] = { ...conversations.value[idx], ...updated }
    }
    if (currentConversation.value?.id === convId) {
      currentConversation.value.title = title
    }
  }

  function clearCurrent() {
    currentConversation.value = null
  }

  return {
    conversations,
    currentConversation,
    loading,
    sortedConversations,
    fetchConversations,
    createConversation,
    selectConversation,
    deleteConversation,
    updateTitle,
    clearCurrent,
  }
})
