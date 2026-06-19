import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Toast } from '../types'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref<Toast[]>([])

  function show(message: string, type: Toast['type'] = 'info') {
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
    toasts.value.push({ id, message, type })
    setTimeout(() => dismiss(id), 3500)
  }

  function dismiss(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return { toasts, show, dismiss }
})