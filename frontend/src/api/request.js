import axios from 'axios'
import { ElMessage } from 'element-plus'
import i18n from '@/i18n'

const { t } = i18n.global

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
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

// Response interceptor
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || t('request.failed'))
      return Promise.reject(new Error(res.message || t('request.failed')))
    }
    return res
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
      return Promise.reject(error)
    }
    const message = error.response?.data?.detail || error.response?.data?.message || error.message || t('request.networkError')
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
