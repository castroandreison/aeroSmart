import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { FinanceiroAPI } from '@/services/api'
import toast from 'react-hot-toast'

export default function AdminFinanceiro() {
  const [financeiro, setFinanceiro] = useState<any[]>([])
  const [resumo, setResumo] = useState<any>(null)
  const [periodo, setPeriodo] = useState({ inicio: '', fim: '' })

  const load = () => FinanceiroAPI.listar().then(setFinanceiro).catch(() => {})

  useEffect(() => { load() }, [])

  const apagarDados = async () => {
    if (!confirm('Apagar TODOS os agendamentos, acionamentos e financeiro? Esta ação é irreversível!')) return
    try {
      const r = await FinanceiroAPI.apagarDados()
      toast.success(`${r.financeiro} financeiro, ${r.acionamentos} acionamentos, ${r.agendamentos} agendamentos apagados!`)
      load()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Erro ao apagar dados') }
  }

  const loadResumo = async () => {
    if (!periodo.inicio || !periodo.fim) return
    try {
      const data = await FinanceiroAPI.resumo(periodo.inicio, periodo.fim)
      setResumo(data)
    } catch { toast.error('Erro ao carregar resumo') }
  }

  return (
    <Layout title="Financeiro">
      <div className="flex justify-end gap-2 mb-4">
        <button onClick={apagarDados} className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded-lg transition text-sm">
          Apagar Dados
        </button>
      </div>

      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Resumo do Período</h3>
        <div className="flex gap-4 mb-4">
          <input type="date" value={periodo.inicio} onChange={(e) => setPeriodo({ ...periodo, inicio: e.target.value })}
            className="px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" />
          <input type="date" value={periodo.fim} onChange={(e) => setPeriodo({ ...periodo, fim: e.target.value })}
            className="px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" />
          <button onClick={loadResumo} className="px-4 py-2 bg-neon-600 hover:bg-neon-500 text-white rounded-lg transition shadow-lg shadow-neon-600/20">
            Calcular
          </button>
        </div>

        {resumo && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="p-4 bg-purple-500/5 border border-purple-500/20 rounded-lg">
              <p className="text-sm text-gray-500">Duração</p>
              <p className="text-xl font-bold text-purple-400">
                {resumo.total_duracao_minutos ? `${Math.floor(resumo.total_duracao_minutos / 60)}h ${Math.round(resumo.total_duracao_minutos % 60)}min` : '0h 0min'}
              </p>
            </div>
            <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
              <p className="text-sm text-gray-500">Energia</p>
              <p className="text-xl font-bold text-yellow-400">{resumo.total_energia_kwh?.toFixed(2)} kWh</p>
            </div>
            <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
              <p className="text-sm text-gray-500">V. Energia</p>
              <p className="text-xl font-bold text-blue-400">R$ {resumo.total_valor_energia?.toFixed(2)}</p>
            </div>
            <div className="p-4 bg-orange-500/5 border border-orange-500/20 rounded-lg">
              <p className="text-sm text-gray-500">V. Acionamento</p>
              <p className="text-xl font-bold text-orange-400">R$ {resumo.total_valor_acionamento?.toFixed(2)}</p>
            </div>
            <div className="p-4 bg-green-500/5 border border-green-500/20 rounded-lg">
              <p className="text-sm text-gray-500">Total</p>
              <p className="text-xl font-bold text-green-400">R$ {resumo.total_receita?.toFixed(2)}</p>
            </div>
          </div>
        )}
      </div>

      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-800">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Data</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Início</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Término</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Duração</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Energia</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">V. Energia</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">V. Acionamento</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {financeiro.map((f: any) => (
              <tr key={f.id} className="hover:bg-dark-800/50">
                <td className="px-4 py-3 text-gray-300 text-sm">{f.data ? new Date(f.data).toLocaleDateString('pt-BR') : '-'}</td>
                <td className="px-4 py-3 text-gray-300 text-sm">{f.hora_inicio ? new Date(f.hora_inicio).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                <td className="px-4 py-3 text-gray-300 text-sm">{f.hora_termino ? new Date(f.hora_termino).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                <td className="px-4 py-3 text-gray-300 text-sm">{f.duracao_minutos ? `${Math.floor(f.duracao_minutos / 60)}h ${Math.round(f.duracao_minutos % 60)}min` : '-'}</td>
                <td className="px-4 py-3 text-gray-300 text-sm">{f.energia_consumida_kwh?.toFixed(2)} kWh</td>
                <td className="px-4 py-3 text-gray-300 text-sm">R$ {f.valor_energia?.toFixed(2)}</td>
                <td className="px-4 py-3 text-gray-300 text-sm">R$ {f.valor_acionamento?.toFixed(2)}</td>
                <td className="px-4 py-3 font-medium text-neon-400 text-sm">R$ {f.valor_total?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
