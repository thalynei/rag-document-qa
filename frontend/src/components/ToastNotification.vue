<script setup lang="ts">
import { CheckCircle, AlertCircle, Info, X } from 'lucide-vue-next'
import { useToastStore } from '../stores/toast'

const toast = useToastStore()

function icon(type: string) {
  if (type === 'success') return CheckCircle
  if (type === 'error') return AlertCircle
  return Info
}
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="t in toast.toasts"
        :key="t.id"
        class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg min-w-[280px] max-w-[420px] border"
        style="background: var(--color-sidebar); border-color: var(--color-border);"
      >
        <component
          :is="icon(t.type)"
          :size="18"
          :class="{
            'text-[var(--color-success)]': t.type === 'success',
            'text-[var(--color-error)]': t.type === 'error',
            'text-[var(--color-primary-light)]': t.type === 'info',
          }"
        />
        <span class="text-sm flex-1 text-[var(--color-text)]">{{ t.message }}</span>
        <button @click="toast.dismiss(t.id)" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors shrink-0">
          <X :size="14" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>