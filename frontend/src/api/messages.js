import api from './index'

export const polishMessage = (data) => api.post('/messages/polish', data)
export const listMessages = () => api.get('/messages')
export const getMessage = (id) => api.get(`/messages/${id}`)
export const deleteMessage = (id) => api.delete(`/messages/${id}`)