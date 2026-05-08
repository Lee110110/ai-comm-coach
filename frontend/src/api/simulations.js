import api from './index'

export const createSimulation = (data) => api.post('/simulations', data)
export const listSimulations = () => api.get('/simulations')
export const getSimulation = (id) => api.get(`/simulations/${id}`)
export const sendMessage = (id, content) => api.post(`/simulations/${id}/messages`, { content })
export const updateDifficulty = (id, difficulty) => api.put(`/simulations/${id}/difficulty`, { difficulty })
export const endSimulation = (id) => api.post(`/simulations/${id}/end`)
export const getDebrief = (id) => api.get(`/simulations/${id}/debrief`)