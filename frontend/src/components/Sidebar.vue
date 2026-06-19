<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  MessageSquare, Plus, FileText, Trash2, Sun, Moon, Download,
  Loader2, Upload, LogOut, User, MessageCircle, Eye, Database,
  Edit2, Check, X
} from 'lucide-vue-next'
import { useChatStore } from '../stores/chat'
import { useThemeStore } from '../stores/theme'
import { useConversationStore } from '../stores/conversation'
import { useAuthStore } from '../stores/auth'
import { useFileUpload } from '../composables/useFileUpload'
import { useToastStore } from '../stores/toast'
import { fetchUserDocuments, deleteUserDocument, type DocumentDetail } from '../services/api'
import DocumentPreview from './DocumentPreview.vue'

defineEmits<{ close: [] }>()

const router = useRouter()
const chatStore = useChatStore()
const themeStore = useThemeStore()
const convStore = useConversationStore()
const authStore = useAuthStore()
const toast = useToastStore()
const { fileInput, triggerFileInput } = useFileUpload()

const showDocs = ref(false)
const dbDocuments = ref<DocumentDetail[]>([])
const loadingDocs = ref(false)
const previewDoc = ref<DocumentDetail | null>(null)

// 重命名相关
const editingConvId = ref<number | null>(null)
const editingTitle = ref('')
const renameInputRef = ref<HTMLInputElement | null>(null)

void fileInput

const PROGRESS_LABELS: Record<string, string> = {
  loading: '正在加载文档...',
  splitting: '正在分块处理...',
  summarizing: '正在生成摘要...',
  embedding: '正在向量化...',
  complete: '处理完成',
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function loadDocuments() {
  loadingDocs.value = true
  try {
    dbDocuments.value = await fetchUserDocuments()
  } catch (e) {
    console.error('加载文档失败:', e)
  } finally {
    loadingDocs.value = false
  }
}

onMounted(() => {
  loadDocuments()
})

async function onNewChat() {
  try {
    await convStore.createConversation()
    chatStore.clearMessages()
  } catch (e) {
    toast.show('创建对话失败', 'error')
  }
}

async function onSelectConv(convId: number) {
  try {
    const conv = await convStore.selectConversation(convId)
    chatStore.clearMessages()
    if (conv.messages) {
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
    toast.show('加载对话失败', 'error')
  }
}

async function onDeleteConv(convId: number, e: Event) {
  e.stopPropagation()
  try {
    await convStore.deleteConversation(convId)
    toast.show('对话已删除', 'info')
  } catch (e) {
    toast.show('删除失败', 'error')
  }
}

function startRename(convId: number, currentTitle: string, e: Event) {
  e.stopPropagation()
  editingConvId.value = convId
  editingTitle.value = currentTitle
  nextTick(() => {
    renameInputRef.value?.focus()
    renameInputRef.value?.select()
  })
}

async function confirmRename(convId: number) {
  if (!editingTitle.value.trim()) {
    editingConvId.value = null
    return
  }
  try {
    await convStore.updateTitle(convId, editingTitle.value.trim())
    toast.show('重命名成功', 'success')
  } catch (e) {
    toast.show('重命名失败', 'error')
  }
  editingConvId.value = null
}

function cancelRename() {
  editingConvId.value = null
}

function handleRenameKeydown(e: KeyboardEvent, convId: number) {
  if (e.key === 'Enter') {
    confirmRename(convId)
  } else if (e.key === 'Escape') {
    cancelRename()
  }
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  const ALLOWED = ['.pdf', '.txt', '.md', '.docx']
  if (!ALLOWED.includes(ext)) {
    toast.show(`不支持的格式: ${ext}`, 'error')
    return
  }
  if (file.size > 50 * 1024 * 1024) {
    toast.show('文件超过 50MB 限制', 'error')
    return
  }
  try {
    const success = await chatStore.upload(file)
    if (success) {
      // 上传完成后重新加载文档列表
      await loadDocuments()
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '上传失败'
    toast.show(msg, 'error')
  }
}

async function onDeleteDoc(docId: string, name: string) {
  try {
    await deleteUserDocument(docId)
    dbDocuments.value = dbDocuments.value.filter(d => d.doc_id !== docId)
    toast.show(`已删除: ${name}`, 'info')
  } catch (e) {
    toast.show('删除失败', 'error')
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar">
    <!-- Header -->
    <div class="sidebar-header">
      <div class="header-logo">
        <MessageSquare :size="16" class="text-white" />
      </div>
      <div class="header-text">
        <h1>RAG Document QA</h1>
        <p>智能文档问答</p>
      </div>
    </div>

    <!-- New Chat -->
    <div class="new-chat-wrapper">
      <button @click="onNewChat" class="new-chat-btn">
        <Plus :size="16" />
        <span>新建对话</span>
      </button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        @click="showDocs = false"
        class="tab"
        :class="{ active: !showDocs }"
      >
        <MessageCircle :size="14" />
        对话
      </button>
      <button
        @click="showDocs = true"
        class="tab"
        :class="{ active: showDocs }"
      >
        <FileText :size="14" />
        文档
      </button>
    </div>

    <!-- Content -->
    <div class="content-area">
      <!-- Conversations -->
      <div v-if="!showDocs" class="list-container">
        <div
          v-for="conv in convStore.sortedConversations"
          :key="conv.id"
          @click="onSelectConv(conv.id)"
          class="conv-item"
          :class="{ active: convStore.currentConversation?.id === conv.id }"
        >
          <MessageCircle :size="15" class="conv-icon" />
          <div class="conv-info">
            <!-- 重命名模式 -->
            <div v-if="editingConvId === conv.id" class="rename-wrapper" @click.stop>
              <input
                ref="renameInputRef"
                v-model="editingTitle"
                class="rename-input"
                @keydown="handleRenameKeydown($event, conv.id)"
                @blur="confirmRename(conv.id)"
              />
              <button @click="confirmRename(conv.id)" class="rename-btn confirm">
                <Check :size="12" />
              </button>
              <button @click="cancelRename" class="rename-btn cancel">
                <X :size="12" />
              </button>
            </div>
            <!-- 正常显示模式 -->
            <template v-else>
              <p class="conv-title">{{ conv.title }}</p>
              <p class="conv-meta">{{ conv.message_count }} 条消息 · {{ formatDate(conv.updated_at) }}</p>
            </template>
          </div>
          <div class="conv-actions" v-if="editingConvId !== conv.id">
            <button
              @click="startRename(conv.id, conv.title, $event)"
              class="conv-action-btn"
              title="重命名"
            >
              <Edit2 :size="12" />
            </button>
            <button
              @click="onDeleteConv(conv.id, $event)"
              class="conv-action-btn delete"
              title="删除"
            >
              <Trash2 :size="12" />
            </button>
          </div>
        </div>

        <div v-if="convStore.conversations.length === 0" class="empty-state">
          <MessageCircle :size="36" class="empty-icon" />
          <p class="empty-title">暂无对话</p>
          <p class="empty-desc">点击上方按钮开始新对话</p>
        </div>
      </div>

      <!-- Documents -->
      <div v-else class="list-container">
        <!-- Knowledge Base Header -->
        <div class="kb-header">
          <div class="kb-info">
            <Database :size="14" />
            <span>知识库</span>
          </div>
          <span class="kb-count">{{ dbDocuments.length }} 个文档</span>
        </div>

        <p class="kb-desc">上传到知识库的文档会被向量化存储，所有对话都可以引用</p>

        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.txt,.md,.docx"
          class="hidden"
          @change="onFileSelected"
        />
        <button @click="triggerFileInput" class="upload-btn">
          <Upload :size="16" />
          <span>上传到知识库</span>
        </button>

        <!-- Loading -->
        <div v-if="loadingDocs" class="loading-state">
          <Loader2 :size="24" class="animate-spin text-[var(--color-primary)]" />
          <p>加载中...</p>
        </div>

        <!-- Uploading -->
        <div
          v-for="uploading in chatStore.uploadingDocs"
          :key="uploading.taskId"
          class="doc-item uploading"
        >
          <Loader2 :size="15" class="animate-spin text-[var(--color-primary)]" />
          <div class="doc-info">
            <p class="doc-name">{{ uploading.filename }}</p>
            <p class="doc-progress">{{ PROGRESS_LABELS[uploading.progress || ''] || '准备中...' }}</p>
            <div class="progress-track">
              <div class="progress-bar" />
            </div>
          </div>
        </div>

        <!-- Documents from DB -->
        <div
          v-for="doc in dbDocuments"
          :key="doc.doc_id"
          class="doc-item"
          @click="previewDoc = doc"
        >
          <FileText :size="15" class="text-[var(--color-primary-light)]" />
          <div class="doc-info">
            <p class="doc-name">{{ doc.filename }}</p>
            <p class="doc-meta">{{ doc.page_count }} 页 · {{ doc.chunk_count }} 块 · 已向量化</p>
          </div>
          <div class="doc-actions">
            <button
              @click.stop="previewDoc = doc"
              class="doc-preview"
              title="预览"
            >
              <Eye :size="13" />
            </button>
            <button
              @click.stop="onDeleteDoc(doc.doc_id, doc.filename)"
              class="doc-delete"
              title="从知识库删除"
            >
              <Trash2 :size="13" />
            </button>
          </div>
        </div>

        <div v-if="!loadingDocs && dbDocuments.length === 0 && chatStore.uploadingDocs.length === 0" class="empty-state">
          <Database :size="36" class="empty-icon" />
          <p class="empty-title">知识库为空</p>
          <p class="empty-desc">上传文档到知识库，AI 可以在所有对话中引用</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="user-card">
        <div class="user-avatar">
          <User :size="14" class="text-white" />
        </div>
        <div class="user-info">
          <p class="user-name">{{ authStore.user?.username || '用户' }}</p>
          <p class="user-email">{{ authStore.user?.email || '' }}</p>
        </div>
      </div>

      <button
        v-if="chatStore.messages.length > 0"
        @click="chatStore.exportConversation"
        class="footer-btn"
      >
        <Download :size="14" />
        <span>导出对话</span>
      </button>

      <button @click="themeStore.toggle()" class="footer-btn">
        <Sun v-if="themeStore.theme === 'dark'" :size="14" />
        <Moon v-else :size="14" />
        <span>{{ themeStore.theme === 'dark' ? '浅色模式' : '深色模式' }}</span>
      </button>

      <button @click="handleLogout" class="footer-btn logout">
        <LogOut :size="14" />
        <span>退出登录</span>
      </button>
    </div>
  </aside>

  <!-- Document Preview Modal -->
  <DocumentPreview
    v-if="previewDoc"
    :doc="previewDoc"
    @close="previewDoc = null"
    @delete="async (docId) => {
      await onDeleteDoc(docId, previewDoc?.filename || '')
      previewDoc = null
    }"
  />
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-sidebar);
  border-right: 1px solid var(--color-border);
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.header-logo {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(108, 99, 255, 0.3);
}

.header-text h1 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.2;
}

.header-text p {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin-top: 0.125rem;
}

/* New Chat */
.new-chat-wrapper {
  padding: 0.75rem;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 12px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  color: white;
  font-size: 0.85rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(108, 99, 255, 0.4);
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0 0.75rem 0.5rem;
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  color: var(--color-text);
}

.tab.active {
  background: var(--color-surface-hover);
  color: var(--color-text);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Content */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0.75rem;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

/* Conversation Item */
.conv-item {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.75rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.conv-item:hover {
  background: var(--color-surface-hover);
}

.conv-item.active {
  background: var(--color-primary-subtle);
  border: 1px solid rgba(108, 99, 255, 0.2);
}

.conv-icon {
  color: var(--color-primary-light);
  margin-top: 0.125rem;
  flex-shrink: 0;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin-top: 0.25rem;
}

/* Conversation Actions */
.conv-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.conv-item:hover .conv-actions {
  opacity: 1;
}

.conv-action-btn {
  padding: 0.25rem;
  border-radius: 6px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.conv-action-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.conv-action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
}

/* Rename */
.rename-wrapper {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.rename-input {
  flex: 1;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--color-primary);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 0.8rem;
  outline: none;
  min-width: 0;
}

.rename-btn {
  padding: 0.25rem;
  border-radius: 4px;
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.rename-btn.confirm {
  color: var(--color-success);
}

.rename-btn.confirm:hover {
  background: rgba(16, 163, 127, 0.1);
}

.rename-btn.cancel {
  color: var(--color-text-muted);
}

.rename-btn.cancel:hover {
  background: var(--color-surface-hover);
}

/* Knowledge Base Header */
.kb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
  margin-bottom: 0.25rem;
}

.kb-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text);
}

.kb-count {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  background: var(--color-surface);
  padding: 0.25rem 0.5rem;
  border-radius: 10px;
}

.kb-desc {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

/* Upload Button */
.upload-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 12px;
  border: 1px dashed var(--color-border);
  color: var(--color-text-secondary);
  background: none;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
  margin-bottom: 0.5rem;
}

.upload-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary-light);
  background: var(--color-primary-subtle);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--color-text-muted);
}

.loading-state p {
  font-size: 0.8rem;
}

/* Document Item */
.doc-item {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.75rem;
  border-radius: 12px;
  transition: all 0.2s;
  cursor: pointer;
}

.doc-item:hover {
  background: var(--color-surface-hover);
}

.doc-item.uploading {
  background: var(--color-primary-subtle);
  cursor: default;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-meta {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin-top: 0.25rem;
}

.doc-progress {
  font-size: 0.7rem;
  color: var(--color-primary-light);
  margin-top: 0.25rem;
}

.progress-track {
  height: 3px;
  background: var(--color-surface);
  border-radius: 2px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.doc-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.doc-item:hover .doc-actions {
  opacity: 1;
}

.doc-preview,
.doc-delete {
  padding: 0.25rem;
  border-radius: 6px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.doc-preview:hover {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.doc-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 1rem;
  text-align: center;
}

.empty-icon {
  color: var(--color-text-muted);
  opacity: 0.2;
  margin-bottom: 1rem;
}

.empty-title {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-bottom: 0.375rem;
}

.empty-desc {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  opacity: 0.5;
  line-height: 1.5;
}

/* Footer */
.sidebar-footer {
  flex-shrink: 0;
  border-top: 1px solid var(--color-border);
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem;
  border-radius: 12px;
  background: var(--color-surface);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-email {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem;
  border-radius: 10px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.footer-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.footer-btn.logout:hover {
  color: #EF4444;
  background: rgba(239, 68, 68, 0.05);
}
</style>
