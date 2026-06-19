<script setup lang="ts">
import { onMounted } from 'vue'
import { useThemeStore } from './stores/theme'
import { useAuthStore } from './stores/auth'

const themeStore = useThemeStore()
const authStore = useAuthStore()

onMounted(() => {
  themeStore.init()
  // Try to restore user session
  if (authStore.token) {
    authStore.fetchUser()
  }
})
</script>

<template>
  <router-view />
</template>