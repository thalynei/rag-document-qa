<script setup lang="ts">
import { computed, type Component } from 'vue'
import { Lightbulb, FileText, Search, HelpCircle } from 'lucide-vue-next'
import { useChatStore } from '../stores/chat'

const emit = defineEmits<{
  select: [question: string]
}>()

const store = useChatStore()

const suggestions = computed(() => {
  const doc = store.documents[0]
  if (doc?.summary) {
    return [
      { text: `请详细解释「${doc.filename}」的核心内容`, icon: 'Lightbulb' },
      { text: '请总结文档的关键要点', icon: 'FileText' },
      { text: '文档中有哪些重要结论？', icon: 'Search' },
      { text: '请用通俗语言解释文档中的专业概念', icon: 'HelpCircle' },
    ]
  }
  return [
    { text: '这份文档的主要内容是什么？', icon: 'Lightbulb' },
    { text: '请总结文档的关键要点', icon: 'FileText' },
    { text: '文档中有哪些重要结论？', icon: 'Search' },
    { text: '请解释文档中提到的核心概念', icon: 'HelpCircle' },
  ]
})

const iconMap: Record<string, Component> = { Lightbulb, FileText, Search, HelpCircle }

function iconComponent(name: string): Component {
  return iconMap[name] || Lightbulb
}
</script>

<template>
  <div class="flex flex-col items-center justify-center px-8 py-16 max-w-3xl mx-auto">
    <!-- Document Summary -->
    <div
      v-if="store.documents[0]?.summary"
      class="w-full mb-12 p-6 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] animate-fade-in-up"
    >
      <p class="text-xs font-semibold text-[var(--color-primary-light)] uppercase tracking-wider mb-3">文档摘要</p>
      <p class="text-base text-[var(--color-text-secondary)] leading-relaxed line-clamp-3">{{ store.documents[0].summary }}</p>
    </div>

    <h2 class="text-2xl font-semibold text-[var(--color-text)] mb-3">开始对话</h2>
    <p class="text-base text-[var(--color-text-muted)] mb-12">选择一个建议问题，或在下方输入你自己的问题</p>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
      <button
        v-for="(s, i) in suggestions"
        :key="s.text"
        @click="emit('select', s.text)"
        class="flex items-start gap-4 p-5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)]/50 hover:bg-[var(--color-surface-hover)] transition-all-smooth text-left group hover-lift animate-fade-in-up"
        :style="{ animationDelay: `${0.1 * i}s` }"
      >
        <div class="w-10 h-10 rounded-lg bg-[var(--color-primary-subtle)] flex items-center justify-center shrink-0 group-hover:bg-[var(--color-primary)] transition-all-smooth group-hover:scale-110">
          <component
            :is="iconComponent(s.icon)"
            :size="20"
            class="text-[var(--color-primary-light)] group-hover:text-white transition-colors"
          />
        </div>
        <span class="text-sm text-[var(--color-text-secondary)] group-hover:text-[var(--color-text)] transition-colors leading-relaxed pt-1.5">
          {{ s.text }}
        </span>
      </button>
    </div>
  </div>
</template>
