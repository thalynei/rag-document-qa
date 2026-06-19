<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { X, FileText, Loader2, Maximize2, Minimize2 } from 'lucide-vue-next'

const props = defineProps<{
  filename: string
  content: string
  loading: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const isMaximized = ref(false)
const modalRef = ref<HTMLElement | null>(null)

// 拖拽相关
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const position = ref({ x: 0, y: 0 })

// 缩放相关
const isResizing = ref(false)
const size = ref({ width: 700, height: 500 })
const resizeStart = ref({ x: 0, y: 0, width: 0, height: 0 })

const displayContent = computed(() => {
  if (!props.content) return '暂无内容'
  return props.content
})

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
              <FileText :size="18" />
            </div>
            <div>
              <h3>{{ filename }}</h3>
              <p class="file-hint">仅用于当前对话，不存储到知识库</p>
            </div>
          </div>
          <div class="header-actions">
            <button @click="toggleMaximize" class="action-btn" title="最大化/还原">
              <Maximize2 v-if="!isMaximized" :size="16" />
              <Minimize2 v-else :size="16" />
            </button>
            <button @click="emit('close')" class="action-btn" title="关闭">
              <X :size="16" />
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="preview-content">
          <div v-if="loading" class="loading-state">
            <Loader2 :size="24" class="animate-spin text-[var(--color-primary)]" />
            <p>加载中...</p>
          </div>
          <pre v-else class="content-text">{{ displayContent }}</pre>
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
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-modal {
  position: fixed;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modal-enter 0.2s ease-out;
  top: 50%;
  left: 50%;
  margin-left: -350px;
  margin-top: -250px;
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
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  user-select: none;
}

.preview-header.draggable {
  cursor: move;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.preview-header h3 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.file-hint {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin: 0.125rem 0 0;
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

.preview-content {
  flex: 1;
  overflow: auto;
  padding: 1.25rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 0.75rem;
  color: var(--color-text-muted);
}

.loading-state p {
  font-size: 0.85rem;
}

.content-text {
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  margin: 0;
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
