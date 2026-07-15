import { useEffect, useState, useCallback } from 'react'
import Layout from '@/components/Layout'
import { AgendamentosAPI, AeronavesAPI } from '@/services/api'
import toast from 'react-hot-toast'

function hojeStr() {
  return new Date().toISOString().slice(0, 10)
}

export default function SolicitanteAgendamentos() {
  const [agendamentos, setAgendamentos] = useState<any[]>([])
  const [aeronaves, setAeronaves] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ data_dia: '', data_mes: '', hora_inicio: '', hora_termino: '', aeronave_id: 0, observacoes: '' })

  const load = useCallback(() => {
    AgendamentosAPI.listar(true).then(setAgendamentos).catch(() => {})
    AeronavesAPI.listar().then(setAeronaves).catch(() => {})
  }, [])

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
    const ano = new Date().getFullYear()
    const data = `${ano}-${String(form.data_mes).padStart(2, '0')}-${String(form.data_dia).padStart(2, '0')}`
    const payload = { data, hora_inicio: form.hora_inicio, hora_termino: form.hora_termino, aeronave_id: form.aeronave_id, observacoes: form.observacoes }
    try {
      await AgendamentosAPI.criar(payload)
      toast.success('Agendamento criado!')
      setShowForm(false)
      setForm({ data_dia: '', data_mes: '', hora_inicio: '', hora_termino: '', aeronave_id: 0, observacoes: '' })
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
        <form onSubmit={handleCreate} className="bg-white rounded-xl shadow-sm p-6 border mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-1">Dia</label>
                <input type="number" min={1} max={31} value={form.data_dia} onChange={(e) => setForm({ ...form, data_dia: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg" required placeholder="DD" />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium mb-1">Mês</label>
                <select value={form.data_mes} onChange={(e) => setForm({ ...form, data_mes: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg" required>
                  <option value="">Mês</option>
                  {[1,2,3,4,5,6,7,8,9,10,11,12].map(m => (
                    <option key={m} value={m}>{String(m).padStart(2, '0')}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Aeronave</label>
              <select value={form.aeronave_id} onChange={(e) => setForm({ ...form, aeronave_id: Number(e.target.value) })}
                className="w-full px-3 py-2 border rounded-lg" required>
                <option value={0}>Selecione</option>
                {aeronaves.map((a: any) => (
                  <option key={a.id} value={a.id}>{a.matricula} - {a.modelo}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Início</label>
              <input type="time" value={form.hora_inicio} onChange={(e) => setForm({ ...form, hora_inicio: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Término</label>
              <input type="time" value={form.hora_termino} onChange={(e) => setForm({ ...form, hora_termino: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Observações</label>
              <textarea value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg" rows={2} />
            </div>
          </div>
          <button type="submit" className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            Agendar
          </button>
        </form>
      )}

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Data/Hora</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Aeronave</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Status</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredAgendamentos.map((a: any) => (
              <tr key={a.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">{new Date(a.hora_inicio).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-3">{a.aeronave_matricula} - {a.aeronave_modelo}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    a.status === 'agendado' ? 'bg-blue-100 text-blue-700' :
                    a.status === 'confirmado' ? 'bg-blue-100 text-blue-700' :
                    a.status === 'em_andamento' ? 'bg-green-100 text-green-700' :
                    a.status === 'aguardando_encerramento' ? 'bg-yellow-100 text-yellow-700' :
                    a.status === 'concluido' ? 'bg-green-100 text-green-700' :
                    a.status === 'falha' ? 'bg-red-100 text-red-700' :
                    'bg-red-100 text-red-700'
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
                    <button onClick={() => handleCancel(a.id)} className="text-red-500 hover:text-red-700 text-sm">
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
