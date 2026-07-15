import { ReactNode, useState } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import {
  LayoutDashboard, Calendar, Plane, Users, Settings, BarChart3,
  Monitor, LogOut, Menu, X, DollarSign, FileText, Wifi, Building2, TrendingUp, Radio, Zap
} from 'lucide-react'

interface LayoutProps {
  children: ReactNode
  title?: string
}

const solicitanteNav = [
  { href: '/solicitante/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/solicitante/agendamentos', label: 'Agendamentos', icon: Calendar },
  { href: '/solicitante/aeronaves', label: 'Minhas Aeronaves', icon: Plane },
  { href: '/solicitante/historico', label: 'Histórico', icon: BarChart3 },
  { href: '/solicitante/relatorios', label: 'Relatórios', icon: FileText },
]

export default function Layout({ children, title }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout, isAdmin } = useAuth()
  const router = useRouter()

  const adminNav = [
    { href: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/admin/agendamentos', label: 'Agendamentos', icon: Calendar },
    ...(user?.nivel_acesso === 'proprietario' ? [{ href: '/admin/dashboard-proprietario', label: 'Visão Geral', icon: TrendingUp }] : []),
    { href: '/admin/usuarios', label: 'Usuários', icon: Users },
    { href: '/admin/aeroclubes', label: 'Aeroclubes', icon: Building2 },
    { href: '/admin/aeronaves', label: 'Aeronaves', icon: Plane },
    { href: '/admin/monitoramento', label: 'Monitoramento', icon: Monitor },
    { href: '/admin/financeiro', label: 'Financeiro', icon: DollarSign },
    { href: '/admin/relatorios', label: 'Relatórios', icon: FileText },
    { href: '/admin/configuracoes', label: 'Configurações', icon: Settings },
    { href: '/admin/mqtt-config', label: 'MQTT Config', icon: Radio },
    { href: '/admin/energia', label: 'Energia', icon: Zap },
    { href: '/admin/logs', label: 'Logs', icon: Wifi },
  ]
  const navItems = isAdmin ? adminNav : solicitanteNav

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <div className="min-h-screen bg-dark-950 lg:flex">
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-dark-900 border-r border-dark-700 transform transition-transform duration-200 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:relative lg:translate-x-0 lg:shrink-0`}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-dark-700">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Plane className="w-6 h-6 text-neon-500" />
            <span><span className="text-neon-500">Aero</span><span className="text-white">Club</span></span>
          </h1>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = router.pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${active ? 'bg-neon-500/10 text-neon-400 border border-neon-500/30' : 'text-gray-400 hover:text-white hover:bg-dark-800'}`}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-dark-700">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <p className="font-medium text-gray-200">{user?.nome}</p>
              <p className="text-gray-500 text-xs capitalize">{user?.nivel_acesso}</p>
            </div>
            <button onClick={handleLogout} className="p-2 text-gray-500 hover:text-neon-400 transition">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0">
        <header className="sticky top-0 z-40 bg-dark-900 border-b border-dark-700 h-16 flex items-center px-6">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden mr-4 text-gray-400 hover:text-white">
            <Menu className="w-6 h-6" />
          </button>
          <h2 className="text-lg font-semibold text-gray-100">{title || 'AeroClub'}</h2>
        </header>

        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
