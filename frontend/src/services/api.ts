import type { UploadTaskResponse, UploadStatusResponse, StatusResponse, Source, ModelInfo, RAGEvaluation } from '../types'

export interface DocumentDetail {
  id: number
  filename: string
  page_count: number
  chunk_count: number
  summary: string | null
  content_preview: string | null
  doc_id: string
  created_at: string
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('rag-qa-token')
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  return {}
}

export interface TempFileResponse {
  temp_id: string
  filename: string
  content_length: number
  message: string
}

export interface TempFileContent {
  filename: string
  content: string
}

export async function uploadDocument(file: File): Promise<UploadTaskResponse> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function checkUploadStatus(taskId: string): Promise<UploadStatusResponse> {
  const res = await fetch(`/api/upload/status/${taskId}`, {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Status check failed' }))
    throw new Error(err.detail || 'Status check failed')
  }
  return res.json()
}

export async function checkStatus(): Promise<StatusResponse> {
  const res = await fetch('/api/status', {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Status check failed: ${res.status}`)
  }
  return res.json()
}

export async function clearDocument(): Promise<void> {
  const res = await fetch('/api/document', {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Clear document failed: ${res.status}`)
  }
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`/api/document/${docId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Delete document failed: ${res.status}`)
  }
}

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch('/api/models', {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`获取模型列表失败: ${res.status}`)
  }
  return res.json()
}

export interface StreamChatCallbacks {
  onToken: (content: string) => void
  onDone: (sources: Source[], evaluation?: RAGEvaluation, model_name?: string) => void
  onError: (error: string) => void
}

export async function streamChat(
  question: string,
  chatHistory: { role: string; content: string }[],
  callbacks: StreamChatCallbacks,
  conversationId?: number,
  model?: string,
): Promise<void> {
  const { onToken, onDone, onError } = callbacks

  let res: Response
  try {
    res = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        question,
        chat_history: chatHistory,
        conversation_id: conversationId,
        model: model || undefined,
      }),
    })
  } catch {
    onError('网络连接失败，请检查后端服务是否运行')
    return
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Chat failed' }))
    onError(err.detail || 'Chat failed')
    return
  }

  if (!res.body) {
    onError('无法读取响应流')
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let doneCalled = false

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const lines = part.split('\n')
      let eventType = ''
      let dataStr = ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7)
        } else if (line.startsWith('data: ')) {
          dataStr = line.slice(6)
        }
      }

      if (!dataStr) continue

      try {
        const data = JSON.parse(dataStr)
        if (eventType === 'token') {
          onToken(data.content)
        } else if (eventType === 'done' && !doneCalled) {
          doneCalled = true
          onDone(data.sources || [], data.evaluation, data.model_name)
        } else if (eventType === 'error') {
          onError(data.error || 'Unknown error')
        }
      } catch {
        // skip malformed JSON
      }
    }
  }

  if (!doneCalled) {
    onDone([])
  }
}

// ─── Document API ────────────────────────────────────────────────────────────

export async function fetchUserDocuments(): Promise<DocumentDetail[]> {
  const res = await fetch('/api/documents', {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`获取文档列表失败: ${res.status}`)
  }
  return res.json()
}

export async function fetchDocumentDetail(docId: string): Promise<DocumentDetail> {
  const res = await fetch(`/api/documents/${docId}`, {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`获取文档详情失败: ${res.status}`)
  }
  return res.json()
}

export async function deleteUserDocument(docId: string): Promise<void> {
  const res = await fetch(`/api/documents/${docId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`删除文档失败: ${res.status}`)
  }
}

export async function fetchDocumentContent(docId: string): Promise<{ filename: string; content: string; total_length: number }> {
  const res = await fetch(`/api/documents/${docId}/content`, {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`获取文档内容失败: ${res.status}`)
  }
  return res.json()
}

// ─── Temporary File API ─────────────────────────────────────────────────────

export async function uploadTempFile(file: File, conversationId?: number): Promise<TempFileResponse> {
  const form = new FormData()
  form.append('file', file)
  const url = conversationId
    ? `/api/upload/temp?conversation_id=${conversationId}`
    : '/api/upload/temp'
  const res = await fetch(url, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function fetchTempFileContent(tempId: string): Promise<TempFileContent> {
  const res = await fetch(`/api/temp/${tempId}/content`, {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`获取临时文件内容失败: ${res.status}`)
  }
  return res.json()
}

// ─── Message API ────────────────────────────────────────────────────────────

export async function deleteMessage(conversationId: number, messageId: number): Promise<void> {
  const res = await fetch(`/api/conversations/${conversationId}/messages/${messageId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`删除消息失败: ${res.status}`)
  }
}

// ─── User Management API ───────────────────────────────────────────────────

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const res = await fetch('/api/auth/change-password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '修改密码失败' }))
    throw new Error(err.detail || '修改密码失败')
  }
}

export async function uploadAvatar(file: File): Promise<{ avatar_url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/auth/avatar', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '上传头像失败' }))
    throw new Error(err.detail || '上传头像失败')
  }
  return res.json()
}

export async function fetchUserSettings(): Promise<{ system_prompt: string }> {
  const res = await fetch('/api/auth/settings', {
    headers: getAuthHeaders(),
  })
  if (!res.ok) {
    throw new Error(`获取设置失败: ${res.status}`)
  }
  return res.json()
}

export async function updateUserSettings(settings: { system_prompt?: string }): Promise<void> {
  const res = await fetch('/api/auth/settings', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(settings),
  })
  if (!res.ok) {
    throw new Error(`更新设置失败: ${res.status}`)
  }
}
