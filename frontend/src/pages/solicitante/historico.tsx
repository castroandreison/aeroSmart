import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { AgendamentosAPI } from '@/services/api'

export default function SolicitanteHistorico() {
  const [agendamentos, setAgendamentos] = useState<any[]>([])

  useEffect(() => {
    const hoje = new Date()
    const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1).toISOString().split('T')[0]
    const fim = hoje.toISOString().split('T')[0]
    AgendamentosAPI.listar({ data_inicio: '2024-01-01', data_fim: fim, status: 'finalizado' })
      .then(setAgendamentos).catch(() => {})
  }, [])

  return (
    <Layout title="Histórico de Voos">
      <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Data</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Início</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Término</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Aeronave</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {agendamentos.map((a: any) => (
              <tr key={a.id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 text-gray-300">{new Date(a.data).toLocaleDateString('pt-BR')}</td>
                <td className="px-4 py-3 text-gray-300">{new Date(a.hora_inicio).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</td>
                <td className="px-4 py-3 text-gray-300">{new Date(a.hora_termino).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</td>
                <td className="px-4 py-3 text-gray-300">{a.aeronave_matricula}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
