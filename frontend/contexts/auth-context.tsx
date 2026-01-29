'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { User, UserRole } from '@/types'
import {
  getAuthToken,
  setAuthToken,
  removeAuthToken,
  isTokenExpired,
  authApi,
} from '@/lib/api'
import { useAuthStore } from '@/lib/store'

const USER_STORAGE_KEY = 'auth_user'
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => void
  hasRole: (role: UserRole) => boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null
  try {
    const stored = localStorage.getItem(USER_STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

function setStoredUser(user: User) {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
}

function removeStoredUser() {
  localStorage.removeItem(USER_STORAGE_KEY)
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // Safe bootstrap (NEVER throws)
  useEffect(() => {
    try {
      const token = getAuthToken()
      const storedUser = getStoredUser()

      if (token && !isTokenExpired(token) && storedUser) {
        setUser(storedUser)
        useAuthStore.getState().setUser(storedUser as any)

        // Background refresh to ensure permissions are up to date
        authApi.getCurrentUser().then((res) => {
          if (res.success && res.data) {
            const freshUser = res.data as unknown as User
            setUser(freshUser)
            setStoredUser(freshUser)
            useAuthStore.getState().setUser(freshUser as any)
          }
        })
      } else {
        removeAuthToken()
        removeStoredUser()
      }
    } catch {
      removeAuthToken()
      removeStoredUser()
    } finally {
      setIsLoading(false)
    }
  }, [])

  // ✅ NO redirects here
  const login = async (email: string, password: string): Promise<User> => {
    // Use centralized API client so token handling stays consistent
    const response = await authApi.login(email, password)

    if (!response.success || !response.data) {
      if (response.error === 'INVALID_CREDENTIALS') {
        throw new Error('INVALID_CREDENTIALS')
      }
      throw new Error('LOGIN_FAILED')
    }

    const { user, token } = response.data

    // Runtime user shape comes from backend serializer; align with frontend `User` via `unknown`.
    const typedUser = user as unknown as User

    setAuthToken(token)
    setStoredUser(typedUser)
    setUser(typedUser)

    // ✅ SYNC: Update useAuthStore so dashboard pages can access user data
    // Cast to any to handle type mismatch between @/types and @/lib/types User definitions
    useAuthStore.getState().setUser(typedUser as any)

    return typedUser
  }

  const logout = () => {
    removeAuthToken()
    removeStoredUser()
    setUser(null)

    // ✅ SYNC: Clear useAuthStore as well
    useAuthStore.getState().setUser(null)

    router.push('/login')
  }

  const hasRole = (role: UserRole) => user?.role === role
  const isAuthenticated = Boolean(user)

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, logout, hasRole, isAuthenticated }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
