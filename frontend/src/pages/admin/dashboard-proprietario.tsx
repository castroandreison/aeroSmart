import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { MonitoramentoAPI } from '@/services/api'
import { Building2, Plane, DollarSign, Zap, Users, Clock } from 'lucide-react'

export default function DashboardProprietario() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    MonitoramentoAPI.dashboardProprietario().then(setData).catch(() => {})
  }, [])

  const cards = [
    { label: 'Aeroclubes', value: data?.total_aeroclubes ?? '...', icon: Building2, color: 'bg-neon-500/10 text-neon-400' },
    { label: 'Total Voos', value: data?.total_voos ?? '...', icon: Plane, color: 'bg-blue-500/10 text-blue-400' },
    { label: 'Total Horas', value: `${data?.total_horas ?? '...'}h`, icon: Clock, color: 'bg-orange-500/10 text-orange-400' },
    { label: 'Energia Total', value: `${data?.total_energia_kwh ?? '...'} kWh`, icon: Zap, color: 'bg-yellow-500/10 text-yellow-400' },
    { label: 'Receita Total', value: `R$ ${data?.total_gasto?.toFixed(2) ?? '...'}`, icon: DollarSign, color: 'bg-green-500/10 text-green-400' },
    { label: 'Usuários Ativos', value: data?.total_usuarios_ativos ?? '...', icon: Users, color: 'bg-purple-500/10 text-purple-400' },
  ]

  return (
    <Layout title="Dashboard do Proprietário">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <div key={card.label} className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 hover:border-dark-600 transition">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{card.label}</p>
                  <p className="text-2xl font-bold mt-1 text-white">{card.value}</p>
                </div>
                <div className={`p-3 rounded-lg ${card.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <h3 className="text-lg font-semibold text-white mb-4">Desempenho por Aeroclube</h3>
      <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Aeroclube</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Voos</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Horas</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Energia (kWh)</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Receita (R$)</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Usuários</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {data?.aeroclubes?.map((ac: any) => (
              <tr key={ac.aeroclube_id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-gray-200">{ac.aeroclube_nome}</td>
                <td className="px-4 py-3 text-right text-gray-300">{ac.total_voos}</td>
                <td className="px-4 py-3 text-right text-gray-300">{ac.total_horas}h</td>
                <td className="px-4 py-3 text-right text-gray-300">{ac.total_energia_kwh}</td>
                <td className="px-4 py-3 text-right text-gray-300">R$ {ac.total_gasto.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-gray-300">{ac.usuarios_ativos}</td>
              </tr>
            ))}
            {(!data?.aeroclubes || data.aeroclubes.length === 0) && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Nenhum aeroclube cadastrado</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
