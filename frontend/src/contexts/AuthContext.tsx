import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { LoginAPI, UsuariosAPI } from '@/services/api'

interface User {
  usuario_id: number
  nome: string
  email: string
  nivel_acesso: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, senha: string) => Promise<void>
  logout: () => void
  updateUser: (data: Partial<User>) => void
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const login = async (email: string, senha: string) => {
    const data = await LoginAPI.login(email, senha)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify({
      usuario_id: data.usuario_id,
      nome: data.nome,
      email: data.email,
      nivel_acesso: data.nivel_acesso,
    }))
    setToken(data.access_token)
    setUser({
      usuario_id: data.usuario_id,
      nome: data.nome,
      email: data.email,
      nivel_acesso: data.nivel_acesso,
    })
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }

  const updateUser = (data: Partial<User>) => {
    setUser((prev) => {
      if (!prev) return null
      const updated = { ...prev, ...data }
      localStorage.setItem('user', JSON.stringify(updated))
      return updated
    })
  }

  const isAdmin = user?.nivel_acesso === 'administrador' || user?.nivel_acesso === 'proprietario'

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, updateUser, isAdmin }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
