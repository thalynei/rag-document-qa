export interface User {
  id: number
  username: string
  email: string
  created_at?: string
}

export interface DocumentItem {
  id: string
  filename: string
  pageCount: number
  chunkCount: number
  summary: string
  uploadedAt: string
}

export interface ApiDocumentItem {
  id: string
  filename: string
  page_count: number
  chunk_count: number
  summary: string
  uploaded_at: string
}

export interface Source {
  source: string
  content: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  isStreaming?: boolean
  timestamp: number
}

export interface ChatHistoryItem {
  role: string
  content: string
}

export interface StatusResponse {
  has_document: boolean
  documents: ApiDocumentItem[]
  filename: string | null
  page_count: number
  chunk_count: number
  summary: string
}

export interface UploadResponse {
  session_id: string
  filename: string
  page_count: number
  chunk_count: number
  summary: string
}

export interface UploadTaskResponse {
  task_id: string
  filename: string
  status: string
}

export interface UploadStatusResponse {
  task_id: string
  filename: string
  status: string
  progress: string | null
  error: string | null
  result: UploadResponse | null
}

export interface UploadingDocument {
  taskId: string
  filename: string
  status: string
  progress: string | null
  error: string | null
}

export interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
}