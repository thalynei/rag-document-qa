<script setup lang="ts">
import { Copy } from 'lucide-vue-next'
import { useToastStore } from '../stores/toast'

const props = defineProps<{
  source: string
  content: string
}>()

const toast = useToastStore()

function copyContent() {
  navigator.clipboard.writeText(props.content)
  toast.show('已复制引用内容', 'success')
}
</script>

<template>
  <div class="group p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-primary)]/30 transition-all-smooth">
    <div class="flex items-start justify-between gap-2">
      <span class="inline-block text-xs font-mono bg-[var(--color-primary-subtle)] text-[var(--color-primary-light)] px-3 py-1 rounded-md">
        {{ source }}
      </span>
      <button
        @click="copyContent"
        class="opacity-0 group-hover:opacity-100 p-2 rounded-lg hover:bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] transition-all-smooth shrink-0"
        title="复制"
      >
        <Copy :size="14" />
      </button>
    </div>
    <p class="text-sm text-[var(--color-text-secondary)] mt-3 leading-relaxed">{{ content }}</p>
  </div>
</template>
