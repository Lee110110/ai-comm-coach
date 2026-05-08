import api from './index'

export const createScenario = (data) => api.post('/scenarios', data)
export const listScenarios = () => api.get('/scenarios')
export const getScenario = (id) => api.get(`/scenarios/${id}`)
export const deleteScenario = (id) => api.delete(`/scenarios/${id}`)