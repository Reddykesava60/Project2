'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
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
  const router = useRouter()
  // Local state for immediate access, but backed by SWR
  const [user, setUser] = useState<User | null>(null)

  // Mounted state to prevent hydration mismatch with localStorage
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  // SWR for background revalidation
  // Only read token after mount to ensure server/client match on first render
  const token = isMounted ? getAuthToken() : null

  const { data: userResponse, mutate } = useSWR(
    token ? '/auth/me/' : null,
    authApi.getCurrentUser,
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
      shouldRetryOnError: false,
      onSuccess: (res) => {
        if (res.success && res.data) {
          const freshUser = res.data as unknown as User

          setUser(freshUser)
          setStoredUser(freshUser)
          useAuthStore.getState().setUser(freshUser as any)
        }
      },
      onError: () => {
        // handle error if needed
      }
    }
  )

  // Initial bootstrap from localStorage or API response
  useEffect(() => {
    if (!isMounted) return

    const storedUser = getStoredUser()
    const storedToken = getAuthToken()

    // Prioritize SWR Response if already available
    if (userResponse?.success && userResponse.data) {
      const freshUser = userResponse.data as unknown as User
      setUser(freshUser)
      setStoredUser(freshUser)
      useAuthStore.getState().setUser(freshUser as any)
      return
    }

    // Fallback to storage
    if (storedToken && !isTokenExpired(storedToken) && storedUser) {
      setUser(storedUser)
      useAuthStore.getState().setUser(storedUser as any)
    } else {
      // Clean start if no token
      if (!storedToken) {
        setUser(null)
        useAuthStore.getState().setUser(null)
      }
    }
  }, [isMounted, userResponse])

  const login = async (email: string, password: string): Promise<User> => {
    const response = await authApi.login(email, password)

    if (!response.success || !response.data) {
      if (response.error === 'INVALID_CREDENTIALS') {
        throw new Error('INVALID_CREDENTIALS')
      }
      throw new Error('LOGIN_FAILED')
    }

    const { user, token } = response.data
    const typedUser = user as unknown as User

    setAuthToken(token)
    setStoredUser(typedUser)
    setUser(typedUser)
    useAuthStore.getState().setUser(typedUser as any)

    // Trigger SWR revalidation
    mutate()

    return typedUser
  }

  const logout = () => {
    removeAuthToken()
    removeStoredUser()
    setUser(null)
    useAuthStore.getState().setUser(null)
    mutate(undefined, false) // Clear SWR cache
    router.push('/login')
  }

  const hasRole = (role: UserRole) => user?.role === role
  const isAuthenticated = Boolean(user)
  // Loading if we are mounted, have a token (conceptually), but no user yet
  const isLoading = isMounted && !!getAuthToken() && !user

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
