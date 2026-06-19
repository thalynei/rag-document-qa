<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { FileText, ChevronDown, ChevronUp, Trash2, X, Maximize2, Minimize2, Loader2, Eye } from 'lucide-vue-next'
import { fetchDocumentContent } from '../services/api'

const props = defineProps<{
  doc: {
    id: number
    filename: string
    page_count: number
    chunk_count: number
    summary: string | null
    content_preview: string | null
    doc_id: string
    created_at: string
  }
}>()

const emit = defineEmits<{
  delete: [docId: string]
  close: []
}>()

const expanded = ref(false)
const isMaximized = ref(false)
const modalRef = ref<HTMLElement | null>(null)
const fullContent = ref('')
const loadingContent = ref(false)
const showFullContent = ref(false)

// 拖拽相关
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const position = ref({ x: 0, y: 0 })

// 缩放相关
const isResizing = ref(false)
const size = ref({ width: 700, height: 600 })
const resizeStart = ref({ x: 0, y: 0, width: 0, height: 0 })

const formattedDate = computed(() => {
  if (!props.doc.created_at) return ''
  const date = new Date(props.doc.created_at)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
})

const previewText = computed(() => {
  if (showFullContent.value && fullContent.value) {
    return fullContent.value
  }
  if (!props.doc.content_preview) return '暂无预览'
  return expanded.value
    ? props.doc.content_preview
    : props.doc.content_preview.slice(0, 500) + (props.doc.content_preview.length > 500 ? '...' : '')
})

async function loadFullContent() {
  if (fullContent.value) {
    showFullContent.value = !showFullContent.value
    return
  }

  loadingContent.value = true
  try {
    const data = await fetchDocumentContent(props.doc.doc_id)
    fullContent.value = data.content
    showFullContent.value = true
  } catch (e) {
    console.error('加载文档内容失败:', e)
  } finally {
    loadingContent.value = false
  }
}

function toggleMaximize() {
  isMaximized.value = !isMaximized.value
}

// 拖拽功能
function startDrag(e: MouseEvent) {
  if (isMaximized.value) return
  isDragging.value = true
  const rect = modalRef.value?.getBoundingClientRect()
  if (rect) {
    dragOffset.value = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    }
  }
}

function onDrag(e: MouseEvent) {
  if (!isDragging.value) return
  position.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y,
  }
}

function stopDrag() {
  isDragging.value = false
}

// 缩放功能
function startResize(e: MouseEvent) {
  if (isMaximized.value) return
  e.preventDefault()
  isResizing.value = true
  resizeStart.value = {
    x: e.clientX,
    y: e.clientY,
    width: size.value.width,
    height: size.value.height,
  }
}

function onResize(e: MouseEvent) {
  if (!isResizing.value) return
  const dx = e.clientX - resizeStart.value.x
  const dy = e.clientY - resizeStart.value.y
  size.value = {
    width: Math.max(400, resizeStart.value.width + dx),
    height: Math.max(300, resizeStart.value.height + dy),
  }
}

function stopResize() {
  isResizing.value = false
}

onMounted(() => {
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<template>
  <Teleport to="body">
    <div class="preview-backdrop" @click.self="emit('close')">
      <div
        ref="modalRef"
        class="preview-modal"
        :class="{ maximized: isMaximized }"
        :style="isMaximized ? {} : {
          width: size.width + 'px',
          height: size.height + 'px',
          transform: `translate(${position.x}px, ${position.y}px)`,
        }"
      >
        <!-- Header (draggable) -->
        <div
          class="preview-header"
          @mousedown="startDrag"
          :class="{ draggable: !isMaximized }"
        >
          <div class="header-left">
            <div class="file-icon">
              <FileText :size="20" />
            </div>
            <div>
              <h3>{{ doc.filename }}</h3>
              <p class="file-meta">{{ formattedDate }} · {{ doc.page_count }} 页 · {{ doc.chunk_count }} 块</p>
            </div>
          </div>
          <div class="header-actions">
            <button @click="loadFullContent" class="action-btn" :title="showFullContent ? '显示摘要' : '查看完整内容'">
              <Loader2 v-if="loadingContent" :size="16" class="animate-spin" />
              <Eye v-else :size="16" />
            </button>
            <button @click="toggleMaximize" class="action-btn" title="最大化/还原">
              <Maximize2 v-if="!isMaximized" :size="16" />
              <Minimize2 v-else :size="16" />
            </button>
            <button @click="emit('close')" class="action-btn" title="关闭">
              <X :size="16" />
            </button>
          </div>
        </div>

        <!-- Stats -->
        <div class="stats-row">
          <div class="stat">
            <span class="stat-value">{{ doc.page_count }}</span>
            <span class="stat-label">页</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ doc.chunk_count }}</span>
            <span class="stat-label">块</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ doc.summary ? '有' : '无' }}</span>
            <span class="stat-label">摘要</span>
          </div>
        </div>

        <!-- Scrollable content -->
        <div class="scroll-area">
          <!-- Summary -->
          <div v-if="doc.summary" class="section">
            <h4>文档摘要</h4>
            <p class="summary-text">{{ doc.summary }}</p>
          </div>

          <!-- Content Preview -->
          <div class="section">
            <div class="section-header">
              <h4>{{ showFullContent ? '完整内容' : '内容预览' }}</h4>
              <div class="section-actions">
                <button
                  v-if="!showFullContent && doc.content_preview && doc.content_preview.length > 500"
                  @click="expanded = !expanded"
                  class="expand-btn"
                >
                  {{ expanded ? '收起' : '展开预览' }}
                  <ChevronUp v-if="expanded" :size="14" />
                  <ChevronDown v-else :size="14" />
                </button>
                <button
                  @click="loadFullContent"
                  class="expand-btn"
                >
                  {{ showFullContent ? '收起内容' : '查看完整内容' }}
                  <ChevronUp v-if="showFullContent" :size="14" />
                  <ChevronDown v-else :size="14" />
                </button>
              </div>
            </div>
            <div class="preview-content">
              <pre>{{ previewText }}</pre>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="actions">
          <button
            @click="emit('delete', doc.doc_id)"
            class="delete-btn"
          >
            <Trash2 :size="16" />
            删除文档
          </button>
        </div>

        <!-- Resize handle -->
        <div
          v-if="!isMaximized"
          class="resize-handle"
          @mousedown="startResize"
        />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.preview-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-modal {
  position: fixed;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modal-enter 0.2s ease-out;
  top: 50%;
  left: 50%;
  margin-left: -350px;
  margin-top: -300px;
}

.preview-modal.maximized {
  inset: 2rem;
  width: auto !important;
  height: auto !important;
  transform: none !important;
  margin: 0;
  top: 2rem;
  left: 2rem;
  right: 2rem;
  bottom: 2rem;
}

@keyframes modal-enter {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  user-select: none;
  flex-shrink: 0;
}

.preview-header.draggable {
  cursor: move;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.preview-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.file-meta {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin: 0.25rem 0 0;
}

.header-actions {
  display: flex;
  gap: 0.375rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.stats-row {
  display: flex;
  gap: 2rem;
  padding: 1rem 1.5rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 0.375rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary);
}

.stat-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.scroll-area {
  flex: 1;
  overflow-y: auto;
}

.section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.section:last-of-type {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.section h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.75rem;
}

.section-header h4 {
  margin-bottom: 0;
}

.section-actions {
  display: flex;
  gap: 0.5rem;
}

.summary-text {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.expand-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.75rem;
  border-radius: 8px;
  font-size: 0.75rem;
  color: var(--color-primary);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.expand-btn:hover {
  background: var(--color-primary-subtle);
}

.preview-content {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.preview-content pre {
  font-size: 0.8rem;
  line-height: 1.7;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  margin: 0;
}

.actions {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.delete-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 10px;
  font-size: 0.85rem;
  color: #EF4444;
  background: rgba(239, 68, 68, 0.1);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* Resize handle */
.resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  background: linear-gradient(
    135deg,
    transparent 50%,
    var(--color-border) 50%,
    var(--color-border) 60%,
    transparent 60%,
    transparent 70%,
    var(--color-border) 70%,
    var(--color-border) 80%,
    transparent 80%
  );
}
</style>
