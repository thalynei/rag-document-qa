<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { Paperclip, FileText, X, ArrowUp, Loader2, Sparkles, Eye } from 'lucide-vue-next'
import { useFileUpload } from '../composables/useFileUpload'
import FilePreviewModal from './FilePreviewModal.vue'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [question: string]
  upload: [file: File]
}>()

const {
  fileInput,
  selectedFile,
  isDragging,
  triggerFileInput,
  clearFile,
  onFileInputChange,
  onDrop,
  onDragOver,
  onDragLeave,
} = useFileUpload()

void fileInput

const inputValue = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const showPreview = ref(false)
const previewContent = ref('')
const previewLoading = ref(false)

const MIN_HEIGHT = 48
const MAX_HEIGHT = 160

const canSend = computed(() => {
  return (inputValue.value.trim().length > 0 || selectedFile.value !== null) && !props.disabled
})

function adjustHeight(reset?: boolean) {
  const textarea = textareaRef.value
  if (!textarea) return
  if (reset) {
    textarea.style.height = `${MIN_HEIGHT}px`
    return
  }
  textarea.style.height = `${MIN_HEIGHT}px`
  const newHeight = Math.max(MIN_HEIGHT, Math.min(textarea.scrollHeight, MAX_HEIGHT))
  textarea.style.height = `${newHeight}px`
}

function handleInput() {
  adjustHeight()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}

function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.kind === 'file') {
      const file = item.getAsFile()
      if (file) {
        e.preventDefault()
        handleFile(file)
        return
      }
    }
  }
}

function handleFile(file: File) {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  const ALLOWED = ['.pdf', '.txt', '.md', '.docx']
  if (!ALLOWED.includes(ext)) return
  if (file.size > 50 * 1024 * 1024) return
  selectedFile.value = file
}

async function previewFile() {
  if (!selectedFile.value) return

  previewLoading.value = true
  showPreview.value = true

  try {
    // 读取文件内容作为预览
    const file = selectedFile.value
    const text = await file.text()
    previewContent.value = text.slice(0, 5000) // 只显示前 5000 字符
  } catch (e) {
    previewContent.value = '无法读取文件内容'
  } finally {
    previewLoading.value = false
  }
}

async function handleSubmit() {
  if (!canSend.value) return
  const file = selectedFile.value
  const question = inputValue.value.trim()
  if (file) {
    emit('upload', file)
    clearFile()
    showPreview.value = false
    previewContent.value = ''
  }
  if (question) {
    emit('send', question)
    inputValue.value = ''
    nextTick(() => adjustHeight(true))
  }
}

function onFileSelected(e: Event) {
  onFileInputChange(e)
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) handleFile(file)
}

function handleDrop(e: DragEvent) {
  onDrop(e)
  const file = e.dataTransfer?.files[0]
  if (file) handleFile(file)
}

watch(() => props.disabled, (val) => {
  if (!val) {
    nextTick(() => textareaRef.value?.focus())
  }
})
</script>

<template>
  <div class="input-area">
    <!-- Drag overlay -->
    <Transition name="fade">
      <div v-if="isDragging" class="drag-overlay">
        <Sparkles :size="24" class="text-[var(--color-primary)]" />
        <p>松开以上传文档</p>
      </div>
    </Transition>

    <!-- File chip -->
    <Transition name="slide-up">
      <div v-if="selectedFile" class="file-chip">
        <FileText :size="16" class="text-[var(--color-primary)]" />
        <div class="file-info">
          <span class="file-name">{{ selectedFile.name }}</span>
          <span class="file-badge">临时文件</span>
        </div>
        <span class="file-size">{{ (selectedFile.size / 1024).toFixed(0) }}KB</span>
        <button @click="previewFile" class="file-preview-btn" title="预览">
          <Eye :size="14" />
        </button>
        <button @click="clearFile; showPreview = false; previewContent = ''" class="file-remove">
          <X :size="14" />
        </button>
      </div>
    </Transition>

    <!-- Input container -->
    <div
      class="input-container"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="handleDrop"
    >
      <div class="input-box" :class="{ focused: !isDragging, dragging: isDragging }">
        <!-- File upload -->
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.txt,.md,.docx"
          class="hidden"
          @change="onFileSelected"
        />
        <button
          @click="triggerFileInput"
          :disabled="disabled"
          class="attach-btn"
          :class="{ active: selectedFile }"
          title="上传文档（仅用于当前对话，不存储到知识库）"
        >
          <Paperclip :size="20" />
        </button>

        <!-- Textarea -->
        <textarea
          ref="textareaRef"
          v-model="inputValue"
          @input="handleInput"
          @keydown="handleKeydown"
          @paste="handlePaste"
          :placeholder="disabled ? 'AI 思考中...' : '输入你的问题...'"
          rows="1"
          :disabled="disabled"
          class="input-textarea"
          :style="{ minHeight: `${MIN_HEIGHT}px`, maxHeight: `${MAX_HEIGHT}px` }"
        />

        <!-- Send button -->
        <button
          @click="handleSubmit"
          :disabled="!canSend"
          class="send-btn"
          :class="{ enabled: canSend }"
          title="发送"
        >
          <Loader2 v-if="disabled" :size="18" class="animate-spin" />
          <ArrowUp v-else :size="20" />
        </button>
      </div>

      <!-- Hint -->
      <p class="input-hint">
        <template v-if="disabled">AI 正在生成回答...</template>
        <template v-else>
          Enter 发送 · Shift + Enter 换行 ·
          <span class="text-[var(--color-primary)]">📎 上传文件仅用于当前对话</span>
        </template>
      </p>
    </div>

    <!-- File Preview Modal -->
    <FilePreviewModal
      v-if="showPreview && selectedFile"
      :filename="selectedFile.name"
      :content="previewContent"
      :loading="previewLoading"
      @close="showPreview = false"
    />
  </div>
</template>

<style scoped>
.input-area {
  position: relative;
}

/* Drag overlay */
.drag-overlay {
  margin: 0 1.5rem 0.75rem;
  padding: 1.25rem;
  border-radius: 16px;
  border: 2px dashed var(--color-primary);
  background: var(--color-primary-subtle);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.drag-overlay p {
  font-size: 0.875rem;
  color: var(--color-primary-light);
}

/* File chip */
.file-chip {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  margin: 0 1.5rem 0.75rem;
  padding: 0.625rem 1rem;
  background: var(--color-primary-subtle);
  border: 1px solid rgba(108, 99, 255, 0.2);
  border-radius: 12px;
  animation: fade-in-up 0.2s ease-out;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.file-name {
  font-size: 0.85rem;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-badge {
  font-size: 0.65rem;
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.1);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  flex-shrink: 0;
}

.file-size {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.file-preview-btn {
  padding: 0.25rem;
  border-radius: 6px;
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.file-preview-btn:hover {
  background: var(--color-primary-subtle);
}

.file-remove {
  padding: 0.25rem;
  border-radius: 6px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.file-remove:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

/* Input container */
.input-container {
  padding: 0 1.5rem 1.5rem;
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 0.625rem;
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  transition: all 0.3s ease;
}

.input-box:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.15), 0 4px 20px rgba(0, 0, 0, 0.1);
}

.input-box.dragging {
  border-color: var(--color-primary);
  background: var(--color-primary-subtle);
}

/* Attach button */
.attach-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.attach-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.attach-btn.active {
  background: var(--color-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(108, 99, 255, 0.3);
}

/* Textarea */
.input-textarea {
  flex: 1;
  background: none;
  border: none;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--color-text);
  resize: none;
  outline: none;
}

.input-textarea::placeholder {
  color: var(--color-text-muted);
}

.input-textarea:disabled {
  opacity: 0.5;
}

/* Send button */
.send-btn {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-active);
  border: none;
  color: var(--color-text-muted);
  cursor: not-allowed;
  transition: all 0.3s ease;
}

.send-btn.enabled {
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(108, 99, 255, 0.4);
}

.send-btn.enabled:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 24px rgba(108, 99, 255, 0.5);
}

.send-btn.enabled:active {
  transform: scale(0.95);
}

/* Hint */
.input-hint {
  text-align: center;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 0.625rem;
  opacity: 0.6;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
