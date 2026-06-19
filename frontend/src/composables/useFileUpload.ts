import { ref } from 'vue'
import { useToastStore } from '../stores/toast'

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx']
const MAX_FILE_SIZE = 50 * 1024 * 1024

export function useFileUpload() {
  const toast = useToastStore()
  const fileInput = ref<HTMLInputElement | null>(null)
  const selectedFile = ref<File | null>(null)
  const isDragging = ref(false)

  function validate(file: File): boolean {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      toast.show(`不支持的格式: ${ext}`, 'error')
      return false
    }
    if (file.size > MAX_FILE_SIZE) {
      toast.show('文件超过 50MB 限制', 'error')
      return false
    }
    return true
  }

  function selectFile(file: File | null) {
    if (!file) return
    if (validate(file)) {
      selectedFile.value = file
    }
  }

  function clearFile() {
    selectedFile.value = null
  }

  function triggerFileInput() {
    fileInput.value?.click()
  }

  function onFileInputChange(e: Event) {
    const input = e.target as HTMLInputElement
    const file = input.files?.[0]
    if (file) selectFile(file)
    input.value = ''
  }

  function onDrop(e: DragEvent) {
    isDragging.value = false
    const file = e.dataTransfer?.files[0]
    if (file) selectFile(file)
  }

  function onDragOver(e: DragEvent) {
    e.preventDefault()
    isDragging.value = true
  }

  function onDragLeave() {
    isDragging.value = false
  }

  return {
    fileInput,
    selectedFile,
    isDragging,
    allowedExtensions: ALLOWED_EXTENSIONS,
    maxFileSize: MAX_FILE_SIZE,
    validate,
    selectFile,
    clearFile,
    triggerFileInput,
    onFileInputChange,
    onDrop,
    onDragOver,
    onDragLeave,
  }
}