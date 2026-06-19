import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<'light' | 'dark'>(
    (localStorage.getItem('rag-qa-theme') as 'light' | 'dark') || 'dark',
  )

  function toggle() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    apply()
  }

  function apply() {
    document.documentElement.setAttribute('data-theme', theme.value)
    localStorage.setItem('rag-qa-theme', theme.value)
  }

  function init() {
    apply()
  }

  return { theme, toggle, init }
})