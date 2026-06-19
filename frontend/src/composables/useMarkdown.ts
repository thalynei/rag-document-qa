import { marked } from 'marked'
import type { RendererObject } from 'marked'
import hljs from 'highlight.js'

// BUG #5 fix: use marked.use() instead of deprecated setOptions()
marked.use({
  breaks: true,
  gfm: true,
})

const renderer: RendererObject = {
  code({ text, lang }: { text: string; lang?: string }): string {
    let highlighted: string
    if (lang && hljs.getLanguage(lang)) {
      highlighted = hljs.highlight(text, { language: lang }).value
    } else {
      highlighted = hljs.highlightAuto(text).value
    }
    return `<pre><code class="hljs language-${lang || 'auto'}">${highlighted}</code></pre>`
  },
}

marked.use({ renderer })

export function useMarkdown() {
  function render(content: string): string {
    return marked.parse(content) as string
  }

  return { render }
}
