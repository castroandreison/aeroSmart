import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { MonitoramentoAPI } from '@/services/api'
import { Plane, Clock, DollarSign, Calendar } from 'lucide-react'

export default function SolicitanteDashboard() {
  const [dashboard, setDashboard] = useState<any>(null)

  useEffect(() => {
    MonitoramentoAPI.dashboardSolicitante().then(setDashboard).catch(() => {})
  }, [])

  return (
    <Layout title="Meu Dashboard">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 hover:border-dark-600 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Próximo Voo</p>
              <p className="text-lg font-bold mt-1 text-white">
                {dashboard?.proximo_voo
                  ? new Date(dashboard.proximo_voo).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
                  : 'Nenhum'}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-neon-500/10 text-neon-400">
              <Plane className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 hover:border-dark-600 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total de Voos</p>
              <p className="text-2xl font-bold mt-1 text-white">{dashboard?.total_voos || 0}</p>
            </div>
            <div className="p-3 rounded-lg bg-green-500/10 text-green-400">
              <Calendar className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 hover:border-dark-600 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Horas Utilizadas</p>
              <p className="text-2xl font-bold mt-1 text-white">{dashboard?.total_horas || '0'}h</p>
            </div>
            <div className="p-3 rounded-lg bg-orange-500/10 text-orange-400">
              <Clock className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 hover:border-dark-600 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Gasto</p>
              <p className="text-2xl font-bold mt-1 text-white">R$ {dashboard?.total_gasto?.toFixed(2) || '0,00'}</p>
            </div>
            <div className="p-3 rounded-lg bg-red-500/10 text-red-400">
              <DollarSign className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Acesso Rápido</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <a href="/solicitante/agendamentos" className="p-4 bg-neon-500/5 border border-neon-500/20 rounded-lg text-center hover:bg-neon-500/10 transition">
            <Calendar className="w-6 h-6 mx-auto text-neon-400" />
            <span className="text-sm mt-1 block text-gray-300">Agendar</span>
          </a>
          <a href="/solicitante/aeronaves" className="p-4 bg-green-500/5 border border-green-500/20 rounded-lg text-center hover:bg-green-500/10 transition">
            <Plane className="w-6 h-6 mx-auto text-green-400" />
            <span className="text-sm mt-1 block text-gray-300">Aeronaves</span>
          </a>
          <a href="/solicitante/historico" className="p-4 bg-purple-500/5 border border-purple-500/20 rounded-lg text-center hover:bg-purple-500/10 transition">
            <Clock className="w-6 h-6 mx-auto text-purple-400" />
            <span className="text-sm mt-1 block text-gray-300">Histórico</span>
          </a>
          <a href="/solicitante/relatorios" className="p-4 bg-orange-500/5 border border-orange-500/20 rounded-lg text-center hover:bg-orange-500/10 transition">
            <DollarSign className="w-6 h-6 mx-auto text-orange-400" />
            <span className="text-sm mt-1 block text-gray-300">Relatórios</span>
          </a>
        </div>
      </div>
    </Layout>
  )
}
