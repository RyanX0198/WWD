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
    return Promise.reject(error)
  }
)

// 写作相关 API
export const generateDocumentApi = (data: any) => api.post('/writing/generate', data)
export const generateOutlineApi = (data: any) => api.post('/writing/outline', data)
export const polishDocumentApi = (data: any) => api.post('/writing/polish', data)

// 知识库相关 API
export const getPeopleListApi = () => api.get('/knowledge/people')
export const getPersonApi = (name: string) => api.get(`/knowledge/people/${name}`)
export const createPersonApi = (data: any) => api.post('/knowledge/people', data)
export const searchPeopleApi = (query: string) => api.get('/knowledge/people/search', { params: { query } })

// 文档相关 API
export const getDocumentsApi = () => api.get('/documents')
export const getDocumentApi = (id: string) => api.get(`/documents/${id}`)
export const createDocumentApi = (data: any) => api.post('/documents', data)
export const updateDocumentApi = (id: string, data: any) => api.put(`/documents/${id}`, data)
export const deleteDocumentApi = (id: string) => api.delete(`/documents/${id}`)

export default api