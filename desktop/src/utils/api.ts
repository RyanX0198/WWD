import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ========== 认证相关 API ==========
export const loginApi = (data: { username: string; password: string }) => api.post('/auth/login', data)
export const registerApi = (data: { username: string; password: string; full_name?: string }) => api.post('/auth/register', data)
export const getMeApi = () => api.get('/auth/me')
export const refreshTokenApi = () => api.post('/auth/refresh')

// ========== 写作相关 API ==========
export const generateDocumentApi = (data: any) => api.post('/writing/generate', data)
export const generateOutlineApi = (data: any) => api.post('/writing/outline', data)
export const polishDocumentApi = (data: any) => api.post('/writing/polish', data)

// ========== 写作风格 API ==========
export const getStylesApi = () => api.get('/styles')
export const getStyleApi = (id: string) => api.get(`/styles/${id}`)
export const createStyleApi = (data: any) => api.post('/styles', data)
export const updateStyleApi = (id: string, data: any) => api.put(`/styles/${id}`, data)
export const deleteStyleApi = (id: string) => api.delete(`/styles/${id}`)
export const learnFromDocumentApi = (id: string, document: string) => api.post(`/styles/${id}/learn`, { document })
export const analyzeDocumentsApi = (id: string, documents: string[]) => api.post(`/styles/${id}/analyze`, documents)
export const getDefaultStylesApi = () => api.get('/styles/defaults/list')

// ========== 多轮对话润色 API ==========
export const createPolishConversationApi = (data: any) => api.post('/polish/conversations', data)
export const getConversationsApi = () => api.get('/polish/conversations')
export const getConversationApi = (id: string) => api.get(`/polish/conversations/${id}`)
export const sendPolishMessageApi = (id: string, data: any) => api.post(`/polish/conversations/${id}/messages`, data)
export const switchPolishModeApi = (id: string, mode: string) => api.post(`/polish/conversations/${id}/mode`, { mode })
export const applyPolishResultApi = (id: string, documentId: string) => api.post(`/polish/conversations/${id}/apply`, { document_id: documentId })

// ========== 知识库 - 人物 API ==========
export const getPeopleListApi = () => api.get('/knowledge/people')
export const getPersonApi = (name: string) => api.get(`/knowledge/people/${name}`)
export const createPersonApi = (data: any) => api.post('/knowledge/people', data)
export const updatePersonApi = (name: string, data: any) => api.put(`/knowledge/people/${name}`, data)
export const deletePersonApi = (name: string) => api.delete(`/knowledge/people/${name}`)
export const searchPeopleApi = (query: string) => api.get('/knowledge/people/search', { params: { query } })

// ========== 知识库 - 机构 API ==========
export const getOrganizationsApi = () => api.get('/orgs')
export const getOrganizationApi = (id: string) => api.get(`/orgs/${id}`)
export const createOrganizationApi = (data: any) => api.post('/orgs', data)
export const updateOrganizationApi = (id: string, data: any) => api.put(`/orgs/${id}`, data)
export const deleteOrganizationApi = (id: string) => api.delete(`/orgs/${id}`)
export const getOrgTreeApi = () => api.get('/orgs/tree')

// ========== 文档管理 API ==========
export const getDocumentsApi = (params?: any) => api.get('/v2/documents', { params })
export const getDocumentApi = (id: string) => api.get(`/v2/documents/${id}`)
export const createDocumentApi = (data: any) => api.post('/v2/documents', data)
export const updateDocumentApi = (id: string, data: any) => api.put(`/v2/documents/${id}`, data)
export const deleteDocumentApi = (id: string) => api.delete(`/v2/documents/${id}`)
export const restoreDocumentApi = (id: string) => api.post(`/v2/documents/${id}/restore`)
export const getDocumentVersionsApi = (id: string) => api.get(`/v2/documents/${id}/versions`)
export const getDocumentVersionApi = (docId: string, versionId: string) => api.get(`/v2/documents/${docId}/versions/${versionId}`)
export const restoreDocumentVersionApi = (docId: string, versionId: string) => api.post(`/v2/documents/${docId}/versions/${versionId}/restore`)

// ========== 模板中心 API ==========
export const getTemplatesApi = () => api.get('/templates')
export const getTemplateApi = (id: string) => api.get(`/templates/${id}`)
export const createTemplateApi = (data: any) => api.post('/templates', data)
export const updateTemplateApi = (id: string, data: any) => api.put(`/templates/${id}`, data)
export const deleteTemplateApi = (id: string) => api.delete(`/templates/${id}`)
export const matchTemplateApi = (docType: string, topic: string) => api.get('/templates/match', { params: { doc_type: docType, topic } })

// ========== 协作编辑 API ==========
export const getCollaborationDocsApi = () => api.get('/collaboration/documents')
export const getCollaborationUsersApi = (docId: string) => api.get(`/collaboration/documents/${docId}/users`)
export const syncCollaborationDocApi = (docId: string) => api.post(`/collaboration/documents/${docId}/sync`)

// ========== 导出 API ==========
export const exportDocumentApi = (id: string, format: 'docx' | 'pdf' = 'docx') => 
  api.get(`/documents/${id}/export`, { 
    params: { format },
    responseType: 'blob'
  })

export default api
