import api from '../utils/axios'

export const getTasks = (projectId, params) =>
  api.get(`/projects/${projectId}/tasks/`, { params })

export const getTask = (projectId, taskId) =>
  api.get(`/projects/${projectId}/tasks/${taskId}`)

export const createTask = (projectId, data) =>
  api.post(`/projects/${projectId}/tasks/`, data)

export const updateTask = (projectId, taskId, data) =>
  api.patch(`/projects/${projectId}/tasks/${taskId}`, data)

export const deleteTask = (projectId, taskId) =>
  api.delete(`/projects/${projectId}/tasks/${taskId}`)
