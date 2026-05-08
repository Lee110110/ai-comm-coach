import api from './index'

export const getCurrentPattern = () => api.get('/patterns/current')
export const getInsights = () => api.get('/patterns/insights')
export const recomputePattern = () => api.post('/patterns/recompute')
export const getTrend = () => api.get('/patterns/trend')
export const markInsightRead = (id) => api.put(`/patterns/insights/${id}/read`)