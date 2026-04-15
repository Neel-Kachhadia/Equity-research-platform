// src/store/useAuthStore.js
// Zustand auth store — persisted to localStorage via token key
// Provides: token, user, login(), logout(), isAuthenticated

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      user:  null,   // { user_id, name, email }

      // Call after successful /auth/login or /auth/register
      _setAuth(data) {
        set({ token: data.token, user: { user_id: data.user_id, name: data.name, email: data.email } })
      },

      // Update profile fields (name, email, role, avatar) — persisted via Zustand
      updateUser(fields) {
        set(s => ({ user: { ...s.user, ...fields } }))
      },

      isAuthenticated() {
        const { token } = get()
        if (!token) return false
        try {
          // Decode payload (no verification — server verifies on every API call)
          const payload = JSON.parse(atob(token.split('.')[1]))
          return payload.exp * 1000 > Date.now()
        } catch {
          return false
        }
      },

      async login(email, password) {
        const res = await fetch(`${API}/auth/login`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ email, password }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Login failed')
        get()._setAuth(data)
        return data
      },

      async register(name, email, password) {
        const res = await fetch(`${API}/auth/register`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ name, email, password }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Registration failed')
        get()._setAuth(data)
        return data
      },

      logout() {
        set({ token: null, user: null })
      },

      // Attach token to any fetch call
      authHeaders() {
        const { token } = get()
        return token ? { Authorization: `Bearer ${token}` } : {}
      },
    }),
    {
      name:    'erebus-auth',           // localStorage key
      partialize: (s) => ({ token: s.token, user: s.user }),
    }
  )
)
