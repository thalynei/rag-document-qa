import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types'

const TOKEN_KEY = 'rag-qa-token'
const USER_KEY = 'rag-qa-user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(null)

  // Load user from localStorage
  try {
    const saved = localStorage.getItem(USER_KEY)
    if (saved) user.value = JSON.parse(saved)
  } catch { /* ignore */ }

  const isAuthenticated = computed(() => !!token.value)

  async function register(username: string, email: string, password: string) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '注册失败' }))
      throw new Error(err.detail || '注册失败')
    }

    const data = await res.json()
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
  }

  async function login(username: string, password: string) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '登录失败' }))
      throw new Error(err.detail || '登录失败')
    }

    const data = await res.json()
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
  }

  async function logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' })
    } catch { /* ignore */ }
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    // 清除聊天记录
    localStorage.removeItem('rag-qa-messages')
  }

  async function fetchUser() {
    if (!token.value) return

    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      if (res.ok) {
        user.value = await res.json()
        localStorage.setItem(USER_KEY, JSON.stringify(user.value))
      } else {
        // Token invalid
        logout()
      }
    } catch { /* ignore */ }
  }

  // Helper to get auth headers
  function authHeaders(): Record<string, string> {
    if (token.value) {
      return { Authorization: `Bearer ${token.value}` }
    }
    return {}
  }

  return {
    token,
    user,
    isAuthenticated,
    register,
    login,
    logout,
    fetchUser,
    authHeaders,
  }
})
