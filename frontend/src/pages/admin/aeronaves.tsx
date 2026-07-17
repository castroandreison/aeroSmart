import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { useAuth } from '@/contexts/AuthContext'
import { AeronavesAPI, AeroclubesAPI } from '@/services/api'
import toast from 'react-hot-toast'

const emptyForm = { matricula: '', modelo: '', fabricante: '', tipo: '', peso_maximo: '', operador: '' }

export default function AdminAeronaves() {
  const { user } = useAuth()
  const isProprietario = user?.nivel_acesso === 'proprietario'
  const [aeronaves, setAeronaves] = useState<any[]>([])
  const [aeroclubes, setAeroclubes] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<any>({ ...emptyForm })
  const [filtroAeroclube, setFiltroAeroclube] = useState('')

  const load = (aeroclube?: string) => {
    const params: any = {}
    if (aeroclube) params.aeroclube_id = aeroclube
    AeronavesAPI.listar(params).then(setAeronaves).catch(() => {})
  }
  const loadAeroclubes = () => AeroclubesAPI.listar().then(setAeroclubes).catch(() => {})
  useEffect(() => { load(); loadAeroclubes() }, [])

  const resetForm = () => { setForm({ ...emptyForm }); setEditingId(null) }

  const openEdit = async (id: number) => {
    try {
      const a = await AeronavesAPI.obter(id)
      setForm({ matricula: a.matricula, modelo: a.modelo, fabricante: a.fabricante || '', tipo: a.tipo || '', peso_maximo: a.peso_maximo || '', operador: a.operador || '' })
      setEditingId(id)
      setShowForm(true)
    } catch { toast.error('Erro ao carregar dados') }
  }

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    try {
      if (editingId) {
        const payload: any = { ...form }
        if (payload.peso_maximo) payload.peso_maximo = Number(payload.peso_maximo)
        await AeronavesAPI.atualizar(editingId, payload)
        toast.success('Aeronave atualizada!')
      } else {
        await AeronavesAPI.criar(form)
        toast.success('Aeronave criada!')
      }
      setShowForm(false)
      resetForm()
      load()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Erro') }
  }

  const handleDelete = async (id: number, matricula: string) => {
    if (!confirm(`Excluir aeronave "${matricula}"?`)) return
    try { await AeronavesAPI.excluir(id); toast.success('Excluída!'); load() }
    catch { toast.error('Erro') }
  }

  return (
    <Layout title="Aeronaves">
      <div className="flex justify-between items-center mb-6">
        <p className="text-gray-500">{aeronaves.length} aeronave(s)</p>
        <div className="flex gap-3 items-center">
          {isProprietario && (
            <select value={filtroAeroclube} onChange={(e) => { setFiltroAeroclube(e.target.value); load(e.target.value) }}
              className="px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100 text-sm">
              <option value="">Todos os Aeroclubes</option>
              {aeroclubes.map((a: any) => <option key={a.id} value={a.id}>{a.nome}</option>)}
            </select>
          )}
          <button onClick={() => { setShowForm(!showForm); if (!showForm) resetForm() }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            {showForm ? 'Fechar' : 'Nova Aeronave'}
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-dark-800 border border-dark-700 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-100 mb-4">{editingId ? 'Editar Aeronave' : 'Nova Aeronave'}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Matrícula *</label>
              <input value={form.matricula} onChange={(e) => setForm({ ...form, matricula: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Modelo *</label>
              <input value={form.modelo} onChange={(e) => setForm({ ...form, modelo: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Fabricante</label>
              <input value={form.fabricante} onChange={(e) => setForm({ ...form, fabricante: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Tipo</label>
              <input value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Peso Máx (kg)</label>
              <input type="number" value={form.peso_maximo} onChange={(e) => setForm({ ...form, peso_maximo: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Operador</label>
              <input value={form.operador} onChange={(e) => setForm({ ...form, operador: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              {editingId ? 'Atualizar' : 'Salvar'}
            </button>
            {editingId && (
              <button type="button" onClick={() => { resetForm(); setShowForm(false) }} className="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600 transition">
                Cancelar
              </button>
            )}
          </div>
        </form>
      )}

      <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Matrícula</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Modelo</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Proprietário</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Fabricante</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Tipo</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Peso Máx</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {aeronaves.map((a: any) => (
              <tr key={a.id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-gray-200">{a.matricula}</td>
                <td className="px-4 py-3 text-gray-300">{a.modelo}</td>
                <td className="px-4 py-3 text-gray-300">{a.usuario_nome || '-'}</td>
                <td className="px-4 py-3 text-gray-300">{a.fabricante || '-'}</td>
                <td className="px-4 py-3 text-gray-300">{a.tipo || '-'}</td>
                <td className="px-4 py-3 text-gray-300">{a.peso_maximo ? `${a.peso_maximo} kg` : '-'}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(a.id)} className="text-blue-400 hover:text-blue-300 text-sm">Editar</button>
                    <button onClick={() => handleDelete(a.id, a.matricula)} className="text-red-400 hover:text-red-300 text-sm">Excluir</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
