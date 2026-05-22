import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Request interceptor — attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle 401 (only for non-login requests)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isLoginRequest = err.config?.url === '/auth/login'
    if (err.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.error('登录已过期，请重新登录')
      // Use a soft redirect that won't hard-refresh the page
      setTimeout(() => {
        window.location.href = '/login'
      }, 1500)
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────
export const login = (data) => api.post('/auth/login', data)
export const getMe = () => api.get('/auth/me')
export const changePassword = (oldPassword, newPassword) =>
  api.post('/auth/change-password', null, { params: { old_password: oldPassword, new_password: newPassword } })

// ── Departments ────────────────────────────────
export const getDepartments = () => api.get('/departments')
export const createDepartment = (data) => api.post('/departments', data)
export const updateDepartment = (id, data) => api.put(`/departments/${id}`, data)
export const deleteDepartment = (id) => api.delete(`/departments/${id}`)

// ── Employees ──────────────────────────────────
export const getEmployees = (params) => api.get('/employees', { params })
export const getEmployee = (id) => api.get(`/employees/${id}`)
export const createEmployee = (data) => api.post('/employees', data)
export const updateEmployee = (id, data) => api.put(`/employees/${id}`, data)
export const deleteEmployee = (id) => api.delete(`/employees/${id}`)
export const createEmployeeAccount = (id, username, password) =>
  api.post(`/employees/${id}/create-account`, null, { params: { username, password } })
export const resetEmployeePassword = (id, password) =>
  api.post(`/employees/${id}/reset-password`, null, { params: { password } })

// ── CheckIn ────────────────────────────────────
export const checkIn = () => api.post('/checkin/in')
export const checkOut = () => api.post('/checkin/out')
export const getTodayStatus = () => api.get('/checkin/today')
export const getCheckinRecords = (params) => api.get('/checkin/records', { params })
export const getCheckinStats = () => api.get('/checkin/stats')
export const getCheckinSettings = () => api.get('/checkin/settings')
export const updateCheckinSettings = (data) => api.put('/checkin/settings', data)
export const updateCheckinStatus = (id, status) => api.put(`/checkin/${id}/status`, { status })

// ── Settings ────────────────────────────────────
export const getSystemSettings = () => api.get('/settings')
export const updateSystemSettings = (data) => api.put('/settings', data)
