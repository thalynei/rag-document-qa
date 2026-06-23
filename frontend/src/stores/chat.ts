import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { Message, DocumentItem, ChatHistoryItem, UploadingDocument, ModelInfo } from '../types'
import { uploadDocument, checkStatus, clearDocument, deleteDocument, streamChat, checkUploadStatus, fetchModels, deleteMessage as apiDeleteMessage } from '../services/api'
import { useToastStore } from './toast'
import { useConversationStore } from './conversation'

const STORAGE_KEY = 'rag-qa-messages'
const MAX_STORED_MESSAGES = 100

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)
  const documents = ref<DocumentItem[]>([])
  const uploadingDocs = ref<UploadingDocument[]>([])
  const pollingTimers = new Map<string, ReturnType<typeof setInterval>>()
  const toast = useToastStore()

  // 模型选择状态
  const selectedModel = ref<string>(localStorage.getItem('rag-qa-model') || '')
  const availableModels = ref<ModelInfo[]>([])

  const hasDocuments = computed(() => documents.value.length > 0)

  async function loadModels() {
    try {
      availableModels.value = await fetchModels()
      // 如果没有选中模型或选中模型不在列表中，使用第一个
      if (availableModels.value.length > 0) {
        const exists = availableModels.value.some(m => m.id === selectedModel.value)
        if (!exists && !selectedModel.value) {
          selectedModel.value = availableModels.value[0].id
        }
      }
    } catch { /* ignore */ }
  }

  function setSelectedModel(modelId: string) {
    selectedModel.value = modelId
    localStorage.setItem('rag-qa-model', modelId)
  }

  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      messages.value = JSON.parse(saved)
    }
  } catch { /* ignore */ }

  watch(
    messages,
    (val) => {
      try {
        const toStore = val.slice(-MAX_STORED_MESSAGES)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore))
      } catch { /* ignore */ }
    },
    { deep: true },
  )

  function genId(): string {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
  }

  async function upload(file: File): Promise<boolean> {
    const res = await uploadDocument(file)
    const uploading: UploadingDocument = {
      taskId: res.task_id,
      filename: res.filename,
      status: 'processing',
      progress: null,
      error: null,
    }
    uploadingDocs.value.push(uploading)

    return new Promise((resolve) => {
      const timer = setInterval(async () => {
        try {
          const status = await checkUploadStatus(res.task_id)
          const idx = uploadingDocs.value.findIndex((d) => d.taskId === res.task_id)
          if (idx === -1) {
            clearInterval(timer)
            resolve(false)
            return
          }

          uploadingDocs.value[idx].status = status.status
          uploadingDocs.value[idx].progress = status.progress
          uploadingDocs.value[idx].error = status.error

          if (status.status === 'completed' && status.result) {
            clearInterval(timer)
            pollingTimers.delete(res.task_id)
            uploadingDocs.value.splice(idx, 1)
            documents.value.push({
              id: status.result.session_id,
              filename: status.result.filename,
              pageCount: status.result.page_count,
              chunkCount: status.result.chunk_count,
              summary: status.result.summary,
              uploadedAt: new Date().toISOString(),
            })
            toast.show(`已上传: ${status.result.filename}`, 'success')
            resolve(true)
          } else if (status.status === 'failed') {
            clearInterval(timer)
            pollingTimers.delete(res.task_id)
            uploadingDocs.value.splice(idx, 1)
            toast.show(`上传失败: ${status.error || '未知错误'}`, 'error')
            resolve(false)
          }
        } catch { /* retry on next interval */ }
      }, 1500)

      pollingTimers.set(res.task_id, timer)
    })
  }

  async function status() {
    try {
      const res = await checkStatus()
      if (res.has_document && res.documents?.length > 0) {
        documents.value = res.documents.map((d) => ({
          id: d.id,
          filename: d.filename,
          pageCount: d.page_count,
          chunkCount: d.chunk_count,
          summary: d.summary,
          uploadedAt: d.uploaded_at,
        }))
      }
    } catch { /* backend unreachable on startup */ }
  }

  async function removeDocument(docId: string) {
    try {
      await deleteDocument(docId)
    } catch { /* server error, still remove locally */ }
    documents.value = documents.value.filter((d) => d.id !== docId)
    if (documents.value.length === 0) {
      messages.value = []
    }
  }

  async function clear() {
    try {
      await clearDocument()
    } catch { /* server error, still clear locally */ }
    documents.value = []
    messages.value = []
    localStorage.removeItem(STORAGE_KEY)
  }

  function clearMessages() {
    messages.value = []
    localStorage.removeItem(STORAGE_KEY)
  }

  async function sendMessage(question: string) {
    const convStore = useConversationStore()

    // 如果没有当前对话，自动创建一个
    if (!convStore.currentConversation) {
      try {
        const title = question.slice(0, 20) + (question.length > 20 ? '...' : '')
        await convStore.createConversation(title)
      } catch (e) {
        console.error('创建对话失败:', e)
      }
    }

    const userMsg: Message = {
      id: genId(),
      role: 'user',
      content: question,
      timestamp: Date.now(),
    }
    messages.value.push(userMsg)

    const assistantMsg: Message = {
      id: genId(),
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: Date.now(),
    }
    messages.value.push(assistantMsg)

    isStreaming.value = true
    const assistantIdx = messages.value.length - 1

    const chatHistory: ChatHistoryItem[] = messages.value
      .slice(0, -2)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      await streamChat(
        question,
        chatHistory,
        {
          onToken: (token) => {
            messages.value[assistantIdx].content += token
          },
          onDone: (sources, evaluation, modelName) => {
            messages.value[assistantIdx].sources = sources
            messages.value[assistantIdx].evaluation = evaluation
            messages.value[assistantIdx].model_name = modelName
            messages.value[assistantIdx].isStreaming = false
            isStreaming.value = false

            // 更新对话列表
            convStore.fetchConversations()
          },
          onError: (error) => {
            messages.value[assistantIdx].content = `生成回答时出错: ${error}`
            messages.value[assistantIdx].isStreaming = false
            isStreaming.value = false
          },
        },
        convStore.currentConversation?.id,
        selectedModel.value || undefined,
      )
    } catch {
      messages.value[assistantIdx].content = '生成回答时出错: 网络连接失败'
      messages.value[assistantIdx].isStreaming = false
      isStreaming.value = false
    }
  }

  async function regenerateMessage(index: number) {
    if (isStreaming.value) return
    const msg = messages.value[index]
    if (!msg || msg.role !== 'assistant') return

    let userMsgIdx = index - 1
    while (userMsgIdx >= 0 && messages.value[userMsgIdx].role !== 'user') {
      userMsgIdx--
    }
    if (userMsgIdx < 0) return

    const userQuestion = messages.value[userMsgIdx].content
    messages.value.splice(userMsgIdx, 2)
    await sendMessage(userQuestion)
  }

  async function deleteMessage(index: number) {
    const msg = messages.value[index]
    if (!msg) return

    // 从本地移除
    messages.value.splice(index, 1)

    // 如果有关联的对话，从服务器也删除
    const convStore = useConversationStore()
    if (convStore.currentConversation && msg.id) {
      try {
        // 尝试用数字 ID 删除（数据库消息 ID）
        const numId = parseInt(msg.id, 10)
        if (!isNaN(numId)) {
          await apiDeleteMessage(convStore.currentConversation.id, numId)
        }
      } catch { /* 忽略服务器错误，本地已删除 */ }
    }
  }

  function exportConversation() {
    if (messages.value.length === 0) return
    const lines = messages.value.map((m) => {
      const role = m.role === 'user' ? '## User' : '## Assistant'
      return `${role}\n\n${m.content}`
    })
    const markdown = `# RAG Document QA - 对话导出\n\n${lines.join('\n\n---\n\n')}`
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rag-qa-export-${new Date().toISOString().slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return {
    messages,
    isStreaming,
    documents,
    uploadingDocs,
    hasDocuments,
    selectedModel,
    availableModels,
    loadModels,
    setSelectedModel,
    upload,
    status,
    removeDocument,
    clear,
    clearMessages,
    sendMessage,
    regenerateMessage,
    deleteMessage,
    exportConversation,
  }
})