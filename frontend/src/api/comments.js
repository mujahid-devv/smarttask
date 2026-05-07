import api from '../utils/axios'

export const getTaskComments = (projectId, taskId) =>
  api.get(`/projects/${projectId}/tasks/${taskId}/comments`)

export const createTaskComment = (projectId, taskId, data) =>
  api.post(`/projects/${projectId}/tasks/${taskId}/comments`, data)

export const editTaskComment = (projectId, taskId, commentId, data) =>
  api.patch(`/projects/${projectId}/tasks/${taskId}/comments/${commentId}`, data)

export const deleteTaskComment = (projectId, taskId, commentId) =>
  api.delete(`/projects/${projectId}/tasks/${taskId}/comments/${commentId}`)
