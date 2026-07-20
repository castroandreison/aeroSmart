import { useEffect, useState, useCallback } from 'react'
import Layout from '@/components/Layout'
import { AgendamentosAPI, AeronavesAPI, AeroclubesAPI } from '@/services/api'
import toast from 'react-hot-toast'

function hojeStr() {
  return new Date().toISOString().slice(0, 10)
}

export default function SolicitanteAgendamentos() {
  const [agendamentos, setAgendamentos] = useState<any[]>([])
  const [aeronaves, setAeronaves] = useState<any[]>([])
  const [aeroclubes, setAeroclubes] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ data_dia: '', data_mes: '', hora_inicio: '', hora_termino: '', aeronave_id: 0, aeroclube_id: 0, observacoes: '' })

  const loadAeronaves = useCallback((aeroclube_id?: number) => {
    const params: any = {}
    if (aeroclube_id) params.aeroclube_id = aeroclube_id
    AeronavesAPI.listar(params).then(setAeronaves).catch(() => {})
  }, [])

  const load = useCallback(() => {
    AgendamentosAPI.listar(true).then(setAgendamentos).catch(() => {})
    loadAeronaves()
    AeroclubesAPI.listar().then(setAeroclubes).catch(() => {})
  }, [loadAeronaves])

  useEffect(() => {
    load()
    const timer = setInterval(load, 30000)
    return () => clearInterval(timer)
  }, [load])

  const hoje = hojeStr()
  const filteredAgendamentos = agendamentos.filter(a => {
    const dataStr = typeof a.data === 'string' ? a.data.slice(0, 10) : new Date(a.data).toISOString().slice(0, 10)
    return dataStr === hoje
  })

  const handleCreate = async (e: any) => {
    e.preventDefault()
    if (!form.aeronave_id || form.aeronave_id === 0) {
      toast.error('Selecione uma aeronave')
      return
    }
    if (!form.aeroclube_id || form.aeroclube_id === 0) {
      toast.error('Selecione um aeroclube')
      return
    }
    const ano = new Date().getFullYear()
    const data = `${ano}-${String(form.data_mes).padStart(2, '0')}-${String(form.data_dia).padStart(2, '0')}`
    const payload = { data, hora_inicio: form.hora_inicio, hora_termino: form.hora_termino, aeronave_id: form.aeronave_id, aeroclube_id: form.aeroclube_id, observacoes: form.observacoes }
    try {
      await AgendamentosAPI.criar(payload)
      toast.success('Agendamento criado!')
      setShowForm(false)
      setForm({ data_dia: '', data_mes: '', hora_inicio: '', hora_termino: '', aeronave_id: 0, aeroclube_id: 0, observacoes: '' })
      load()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Erro') }
  }

  const handleCancel = async (id: number) => {
    if (!confirm('Cancelar agendamento?')) return
    try {
      await AgendamentosAPI.cancelar(id)
      toast.success('Cancelado!')
      load()
    } catch { toast.error('Erro') }
  }

  return (
    <Layout title="Meus Agendamentos">
      <div className="flex justify-between items-center mb-6">
        <p className="text-gray-500">{filteredAgendamentos.length} agendamento(s)</p>
        <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
          {showForm ? 'Fechar' : 'Novo Agendamento'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-dark-800 border border-dark-700 rounded-xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-400 mb-1">Dia</label>
                <input type="number" min={1} max={31} value={form.data_dia} onChange={(e) => setForm({ ...form, data_dia: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required placeholder="DD" />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-400 mb-1">Mês</label>
                <select value={form.data_mes} onChange={(e) => setForm({ ...form, data_mes: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required>
                  <option value="">Mês</option>
                  {[1,2,3,4,5,6,7,8,9,10,11,12].map(m => (
                    <option key={m} value={m}>{String(m).padStart(2, '0')}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Aeronave</label>
              <select value={form.aeronave_id} onChange={(e) => setForm({ ...form, aeronave_id: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required>
                <option value={0}>Selecione</option>
                {aeronaves.map((a: any) => (
                  <option key={a.id} value={a.id}>{a.matricula} - {a.modelo}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Aeroclube</label>
              <select value={form.aeroclube_id} onChange={(e) => { const id = Number(e.target.value); setForm({ ...form, aeroclube_id: id, aeronave_id: 0 }); loadAeronaves(id || undefined) }}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required>
                <option value={0}>Selecione</option>
                {aeroclubes.map((a: any) => (
                  <option key={a.id} value={a.id}>{a.nome}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-400 mb-1">Início</label>
                <input type="time" value={form.hora_inicio} onChange={(e) => setForm({ ...form, hora_inicio: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-400 mb-1">Término</label>
                <input type="time" value={form.hora_termino} onChange={(e) => setForm({ ...form, hora_termino: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
              </div>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-400 mb-1">Observações</label>
              <textarea value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" rows={2} />
            </div>
          </div>
          <button type="submit" disabled={!form.aeronave_id || form.aeronave_id === 0 || !form.aeroclube_id || form.aeroclube_id === 0}
            className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg transition">
            Agendar
          </button>
        </form>
      )}

      <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Data/Hora</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Aeroclube</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Aeronave</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Status</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {filteredAgendamentos.map((a: any) => (
              <tr key={a.id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 text-gray-300">{new Date(a.hora_inicio).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-3 text-gray-300">{a.aeroclube_nome || '-'}</td>
                <td className="px-4 py-3 text-gray-300">{a.aeronave_matricula} - {a.aeronave_modelo}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    a.status === 'agendado' ? 'bg-blue-900/50 text-blue-400' :
                    a.status === 'confirmado' ? 'bg-blue-900/50 text-blue-400' :
                    a.status === 'em_andamento' ? 'bg-green-900/50 text-green-400' :
                    a.status === 'aguardando_encerramento' ? 'bg-yellow-900/50 text-yellow-400' :
                    a.status === 'concluido' ? 'bg-green-900/50 text-green-400' :
                    a.status === 'falha' ? 'bg-red-900/50 text-red-400' :
                    'bg-red-900/50 text-red-400'
                  }`}>
                    {a.status === 'agendado' ? 'Agendado' :
                     a.status === 'confirmado' ? 'Confirmado' :
                     a.status === 'em_andamento' ? 'Em Andamento' :
                     a.status === 'aguardando_encerramento' ? 'Aguardando Encerramento' :
                     a.status === 'concluido' ? 'Concluído' :
                     a.status === 'falha' ? 'Falha' :
                     'Cancelado'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {a.status === 'agendado' && (
                    <button onClick={() => handleCancel(a.id)} className="text-red-400 hover:text-red-300 text-sm">
                      Cancelar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
