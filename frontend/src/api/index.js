import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  // 文件上传
  uploadFiles(files) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    return api.post('/upload/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 搜索
  search(query, mode = 'text', limit = 10) {
    return api.post('/search/', { query, mode, limit })
  },

  // 文件列表
  getFiles(page = 1, pageSize = 20, docType = null) {
    return api.get('/files/list', {
      params: { page, page_size: pageSize, doc_type: docType }
    })
  },

  // 文件预览
  previewFile(fileHash) {
    return api.get(`/files/preview/${fileHash}`)
  },

  // 删除文件
  deleteFile(fileHash) {
    return api.delete(`/files/${fileHash}`)
  },

  // 仪表盘统计
  getDashboardStats() {
    return api.get('/dashboard/stats')
  },

  // 趋势数据
  getTrend(days = 7) {
    return api.get('/dashboard/trend', { params: { days } })
  },

  // 文件类型分布
  getFileTypes() {
    return api.get('/dashboard/file-types')
  },

  // 实体数据
  getEntities(fileHash = null) {
    return api.get('/dashboard/entities', {
      params: fileHash ? { file_hash: fileHash } : {}
    })
  },

  // 系统资源
  getSystemResources() {
    return api.get('/system/resources')
  },

  // 系统状态
  getSystemStatus() {
    return api.get('/system/status')
  },

  // 日志
  getLogs(lines = 500) {
    return api.get('/system/logs', { params: { lines } })
  }
}
