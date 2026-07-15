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
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Data</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Início</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Término</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Aeronave</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {agendamentos.map((a: any) => (
              <tr key={a.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">{new Date(a.data).toLocaleDateString('pt-BR')}</td>
                <td className="px-4 py-3">{new Date(a.hora_inicio).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</td>
                <td className="px-4 py-3">{new Date(a.hora_termino).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</td>
                <td className="px-4 py-3">{a.aeronave_matricula}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
