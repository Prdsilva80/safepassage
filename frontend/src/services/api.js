import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  anonymous: () => api.post('/auth/anonymous'),
  me: () => api.get('/auth/me'),
}

export const reportsAPI = {
  nearby: (lat, lng, radius_km = 10) => api.get('/reports/nearby', { params: { lat, lng, radius_km } }),
  create: (data) => api.post('/reports/', data),
  confirm: (id, confirms) => api.post(`/reports/${id}/confirm`, { confirms }),
}

export const sheltersAPI = {
  nearby: (lat, lng, radius_km = 30) => api.get('/shelters/nearby', { params: { lat, lng, radius_km } }),
  create: (data) => api.post('/shelters/', data),
  update: (id, data) => api.patch(`/shelters/${id}`, data),
}

export const sosAPI = {
  trigger: (data) => api.post('/sos/', data),
  active: () => api.get('/sos/active'),
  acknowledge: (id, org_name) => api.patch(`/sos/${id}/acknowledge`, null, { params: { org_name } }),
  resolve: (id) => api.patch(`/sos/${id}/resolve`),
}

export const zonesAPI = {
  list: () => api.get('/zones/'),
  create: (data) => api.post('/zones/', data),
}

export const aiAPI = {
  assess: (data) => api.post('/ai/risk-assessment', data),
}

export default api
