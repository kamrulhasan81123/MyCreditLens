"use client"

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react"
import {
  authApi,
  getAccessToken,
  setTokens,
  clearTokens,
  type UserProfile,
} from "@/lib/api-client"
import { getSupabaseClient } from "@/lib/supabase-client"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AuthState {
  user: UserProfile | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<UserProfile>
  register: (data: { email: string; password: string; full_name: string; role: string }) => Promise<void>
  logout: () => void
  clearError: () => void
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  })

  // Check for existing session on mount
  useEffect(() => {
    const supabase = getSupabaseClient()
    const loadProfile = async (accessToken?: string, refreshToken?: string) => {
      if (accessToken && refreshToken) setTokens(accessToken, refreshToken)
      if (!getAccessToken()) {
        setState((prev) => ({ ...prev, isLoading: false }))
        return
      }
      try {
        const user = await authApi.me()
        setState({ user, isLoading: false, isAuthenticated: true, error: null })
      } catch {
        clearTokens()
        setState({ user: null, isLoading: false, isAuthenticated: false, error: null })
      }
    }
    if (!supabase) {
      void loadProfile()
      return
    }
    void supabase.auth.getSession().then(({ data }) => {
      void loadProfile(data.session?.access_token, data.session?.refresh_token)
    })
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setTokens(session.access_token, session.refresh_token)
      } else {
        clearTokens()
      }
    })
    return () => listener.subscription.unsubscribe()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const supabase = getSupabaseClient()
      if (supabase) {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password })
        if (error || !data.session) throw { detail: error?.message || "Supabase login failed" }
        setTokens(data.session.access_token, data.session.refresh_token)
      } else {
        const tokens = await authApi.login({ email, password })
        setTokens(tokens.access_token, tokens.refresh_token)
      }
      const user = await authApi.me()
      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      })
      return user
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err?.detail || "Login failed",
      }))
      throw err
    }
  }, [])

  const register = useCallback(
    async (data: { email: string; password: string; full_name: string; role: string }) => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }))
      try {
        const supabase = getSupabaseClient()
        if (supabase) {
          const result = await supabase.auth.signUp({
            email: data.email,
            password: data.password,
            options: { data: { full_name: data.full_name } },
          })
          if (result.error) throw { detail: result.error.message }
          if (!result.data.session) {
            setState((prev) => ({ ...prev, isLoading: false }))
            return
          }
          setTokens(result.data.session.access_token, result.data.session.refresh_token)
        } else {
          const tokens = await authApi.register(data)
          setTokens(tokens.access_token, tokens.refresh_token)
        }
        const user = await authApi.me()
        setState({
          user,
          isLoading: false,
          isAuthenticated: true,
          error: null,
        })
      } catch (err: any) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err?.detail || "Registration failed",
        }))
        throw err
      }
    },
    []
  )

  const logout = useCallback(() => {
    void getSupabaseClient()?.auth.signOut()
    clearTokens()
    setState({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,
    })
  }, [])

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }))
  }, [])

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
