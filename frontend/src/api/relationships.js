import api from './index'

export const createRelationship = (data) => api.post('/relationships', data)
export const listRelationships = () => api.get('/relationships')
export const getRelationship = (id) => api.get(`/relationships/${id}`)
export const updateRelationship = (id, data) => api.put(`/relationships/${id}`, data)
export const deleteRelationship = (id) => api.delete(`/relationships/${id}`)
export const getStrategy = (id) => api.get(`/relationships/${id}/strategy`)