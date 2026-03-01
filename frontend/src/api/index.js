import request from './request'

// ==================== 实例管理 ====================
export const instanceApi = {
  list: (params) => request.get('/instances', { params }),
  get: (id) => request.get(`/instances/${id}`),
  create: (data) => request.post('/instances', data),
  update: (id, data) => request.put(`/instances/${id}`, data),
  delete: (id) => request.delete(`/instances/${id}`),
  checkHealth: (id) => request.post(`/instances/${id}/health-check`),
}

// ==================== 模型管理 ====================
export const modelApi = {
  list: (params) => request.get('/models', { params }),
  get: (id) => request.get(`/models/${id}`),
  create: (data) => request.post('/models', data),
  update: (id, data) => request.put(`/models/${id}`, data),
  delete: (id) => request.delete(`/models/${id}`),
  // 模型供应商
  listProviders: (params) => request.get('/models/providers', { params }),
  createProvider: (data) => request.post('/models/providers', data),
  updateProvider: (id, data) => request.put(`/models/providers/${id}`, data),
  deleteProvider: (id) => request.delete(`/models/providers/${id}`),
  // 参数模板
  listTemplates: (params) => request.get('/models/templates', { params }),
  createTemplate: (data) => request.post('/models/templates', data),
  updateTemplate: (id, data) => request.put(`/models/templates/${id}`, data),
  deleteTemplate: (id) => request.delete(`/models/templates/${id}`),
}

// ==================== Agent管理 ====================
export const agentApi = {
  list: (params) => request.get('/agents', { params }),
  get: (id) => request.get(`/agents/${id}`),
  create: (data) => request.post('/agents', data),
  update: (id, data) => request.put(`/agents/${id}`, data),
  delete: (id) => request.delete(`/agents/${id}`),
  start: (id) => request.post(`/agents/${id}/start`),
  stop: (id) => request.post(`/agents/${id}/stop`),
  restart: (id) => request.post(`/agents/${id}/restart`),
  copy: (id, data) => request.post(`/agents/${id}/copy`, data),
  // Skills binding
  listSkills: (id) => request.get(`/agents/${id}/skills`),
  bindSkill: (id, data) => request.post(`/agents/${id}/skills`, data),
  unbindSkill: (agentId, skillId) => request.delete(`/agents/${agentId}/skills/${skillId}`),
}

// ==================== Skills管理 ====================
export const skillApi = {
  list: (params) => request.get('/skills', { params }),
  get: (id) => request.get(`/skills/${id}`),
  create: (data) => request.post('/skills', data),
  update: (id, data) => request.put(`/skills/${id}`, data),
  delete: (id) => request.delete(`/skills/${id}`),
  install: (id) => request.post(`/skills/${id}/install`),
  uninstall: (id) => request.post(`/skills/${id}/uninstall`),
}

// ==================== 输出管理 ====================
export const outputApi = {
  list: (params) => request.get('/outputs', { params }),
  get: (id) => request.get(`/outputs/${id}`),
  search: (params) => request.get('/outputs/search', { params }),
  addTag: (id, data) => request.post(`/outputs/${id}/tags`, data),
  removeTag: (id, tagId) => request.delete(`/outputs/${id}/tags/${tagId}`),
  toggleFavorite: (id) => request.post(`/outputs/${id}/favorite`),
  export: (id, format) => request.get(`/outputs/${id}/export`, { params: { format }, responseType: 'blob' }),
}

// ==================== 协作配置 ====================
export const collaborationApi = {
  list: (params) => request.get('/collaborations', { params }),
  get: (id) => request.get(`/collaborations/${id}`),
  create: (data) => request.post('/collaborations', data),
  update: (id, data) => request.put(`/collaborations/${id}`, data),
  delete: (id) => request.delete(`/collaborations/${id}`),
  // 模板
  listTemplates: (params) => request.get('/collaborations/templates', { params }),
  saveAsTemplate: (id) => request.post(`/collaborations/${id}/save-template`),
}

// ==================== 共享记忆池 ====================
export const memoryPoolApi = {
  list: (params) => request.get('/memory-pools', { params }),
  get: (id) => request.get(`/memory-pools/${id}`),
  create: (data) => request.post('/memory-pools', data),
  update: (id, data) => request.put(`/memory-pools/${id}`, data),
  delete: (id) => request.delete(`/memory-pools/${id}`),
  // Agent bindings
  listAgents: (id) => request.get(`/memory-pools/${id}/agents`),
  bindAgent: (id, data) => request.post(`/memory-pools/${id}/agents`, data),
  unbindAgent: (poolId, agentId) => request.delete(`/memory-pools/${poolId}/agents/${agentId}`),
}

// ==================== 仪表盘 ====================
export const dashboardApi = {
  getOverview: () => request.get('/dashboard/overview'),
  getRecentOutputs: (params) => request.get('/dashboard/recent-outputs', { params }),
  getAlerts: () => request.get('/dashboard/alerts'),
}

// ==================== 系统设置 ====================
export const systemApi = {
  getInfo: () => request.get('/system/info'),
  getSettings: () => request.get('/system/settings'),
  updateSettings: (data) => request.put('/system/settings', data),
}
