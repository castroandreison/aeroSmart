import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { AeronavesAPI } from '@/services/api'
import toast from 'react-hot-toast'

export default function SolicitanteAeronaves() {
  const [aeronaves, setAeronaves] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ matricula: '', modelo: '', fabricante: '', tipo: '', peso_maximo: '' })

  const load = () => AeronavesAPI.listar().then(setAeronaves).catch(() => {})
  useEffect(() => { load() }, [])

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    try {
      await AeronavesAPI.criar(form)
      toast.success('Aeronave adicionada!')
      setShowForm(false)
      setForm({ matricula: '', modelo: '', fabricante: '', tipo: '', peso_maximo: '' })
      load()
    } catch { toast.error('Erro ao criar') }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Excluir aeronave?')) return
    try { await AeronavesAPI.excluir(id); toast.success('Excluída!'); load() }
    catch { toast.error('Erro') }
  }

  return (
    <Layout title="Minhas Aeronaves">
      <div className="flex justify-between items-center mb-6">
        <p className="text-gray-500">{aeronaves.length} aeronave(s)</p>
        <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
          {showForm ? 'Fechar' : 'Adicionar Aeronave'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-dark-800 border border-dark-700 rounded-xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Matrícula</label>
              <input value={form.matricula} onChange={(e) => setForm({ ...form, matricula: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Modelo</label>
              <input value={form.modelo} onChange={(e) => setForm({ ...form, modelo: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Fabricante</label>
              <input value={form.fabricante} onChange={(e) => setForm({ ...form, fabricante: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Peso Máx (kg)</label>
              <input type="number" value={form.peso_maximo} onChange={(e) => setForm({ ...form, peso_maximo: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
          </div>
          <button type="submit" className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">Salvar</button>
        </form>
      )}

      <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Matrícula</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Modelo</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Fabricante</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {aeronaves.map((a: any) => (
              <tr key={a.id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-gray-200">{a.matricula}</td>
                <td className="px-4 py-3 text-gray-300">{a.modelo}</td>
                <td className="px-4 py-3 text-gray-300">{a.fabricante || '-'}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => handleDelete(a.id)} className="text-red-400 hover:text-red-300 text-sm">Excluir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
