import { useState, FormEvent } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'
import { Plane } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login, user } = useAuth()
  const router = useRouter()

  if (user) {
    router.push(user.nivel_acesso === 'administrador' ? '/admin/dashboard' : '/solicitante/dashboard')
    return null
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await login(email, senha)
      toast.success('Login realizado com sucesso!')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao fazer login')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neon-500/5 via-transparent to-transparent" />
      <div className="bg-dark-900 border border-dark-700 rounded-2xl shadow-2xl p-8 w-full max-w-md relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-neon-500/10 border border-neon-500/30 mb-4">
            <Plane className="w-8 h-8 text-neon-400" />
          </div>
          <h1 className="text-3xl font-bold">
            <span className="text-neon-500">Aero</span><span className="text-white">Club</span>
          </h1>
          <p className="text-gray-500 mt-2">Automação de Balizamento</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg focus:ring-2 focus:ring-neon-500 focus:border-neon-500 text-gray-100 placeholder-gray-500 transition"
              placeholder="seu@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Senha</label>
            <input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg focus:ring-2 focus:ring-neon-500 focus:border-neon-500 text-gray-100 placeholder-gray-500 transition"
              placeholder="Sua senha"
              required
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 bg-neon-600 hover:bg-neon-500 text-white font-medium rounded-lg transition disabled:opacity-50 shadow-lg shadow-neon-600/20"
          >
            {submitting ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
