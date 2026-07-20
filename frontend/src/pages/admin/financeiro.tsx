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

  const gerarDados = async () => {
    try {
      const r = await FinanceiroAPI.gerarDadosTeste()
      toast.success(`${r.agendamentos_passados} passados + ${r.agendamentos_futuros} futuros criados!`)
      load()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Erro ao gerar dados') }
  }

  const apagarDados = async () => {
    if (!confirm('Apagar todos os dados de teste (agendamentos, acionamentos e financeiro)?')) return
    try {
      const r = await FinanceiroAPI.apagarDados()
      toast.success(`${r.agendamentos} agendamentos apagados!`)
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
        <button onClick={gerarDados} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition text-sm">
          Gerar Dados de Teste
        </button>
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-green-500/5 border border-green-500/20 rounded-lg">
              <p className="text-sm text-gray-500">Receita</p>
              <p className="text-xl font-bold text-green-400">R$ {resumo.total_receita.toFixed(2)}</p>
            </div>
            <div className="p-4 bg-neon-500/5 border border-neon-500/20 rounded-lg">
              <p className="text-sm text-gray-500">Acionamentos</p>
              <p className="text-xl font-bold text-neon-400">{resumo.total_acionamentos}</p>
            </div>
            <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
              <p className="text-sm text-gray-500">Energia</p>
              <p className="text-xl font-bold text-yellow-400">{resumo.total_energia_kwh} kWh</p>
            </div>
            <div className="p-4 bg-purple-500/5 border border-purple-500/20 rounded-lg">
              <p className="text-sm text-gray-500">Horas</p>
              <p className="text-xl font-bold text-purple-400">{resumo.total_horas}h</p>
            </div>
          </div>
        )}
      </div>

      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-800">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Agendamento</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Energia</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Valor Energia</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Valor Acionamento</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {financeiro.map((f: any) => (
              <tr key={f.id} className="hover:bg-dark-800/50">
                <td className="px-4 py-3 text-gray-300">#{f.agendamento_id}</td>
                <td className="px-4 py-3 text-gray-300">{f.energia_consumida_kwh?.toFixed(2)} kWh</td>
                <td className="px-4 py-3 text-gray-300">R$ {f.valor_energia?.toFixed(2)}</td>
                <td className="px-4 py-3 text-gray-300">R$ {f.valor_acionamento?.toFixed(2)}</td>
                <td className="px-4 py-3 font-medium text-neon-400">R$ {f.valor_total?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
