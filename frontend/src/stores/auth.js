import { defineStore } from 'pinia'
import { login, register, getMe } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    async login(username, password) {
      const res = await login({ username, password })
      this.token = res.data.access_token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
    },
    async register(username, password, email, display_name) {
      const res = await register({ username, password, email, display_name })
      this.token = res.data.access_token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
    },
    async fetchUser() {
      if (!this.token) return
      try {
        const res = await getMe()
        this.user = res.data
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    },
  },
})