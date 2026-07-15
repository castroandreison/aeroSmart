import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { useAuth } from '@/contexts/AuthContext'
import { AeroclubesAPI } from '@/services/api'
import toast from 'react-hot-toast'

export default function AdminAeroclubes() {
  const { user } = useAuth()
  const isProprietario = user?.nivel_acesso === 'proprietario'
  const [aeroclubes, setAeroclubes] = useState<any[]>([])
  const [nome, setNome] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [filtroAeroclube, setFiltroAeroclube] = useState('')

  const load = () => AeroclubesAPI.listar().then(setAeroclubes).catch(() => {})
  useEffect(() => { load() }, [])

  const reset = () => { setNome(''); setEditingId(null) }

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    if (!nome.trim()) { toast.error('Informe o nome do aeroclube'); return }
    try {
      if (editingId) {
        await AeroclubesAPI.atualizar(editingId, { nome: nome.trim() })
        toast.success('Aeroclube atualizado!')
      } else {
        await AeroclubesAPI.criar({ nome: nome.trim() })
        toast.success('Aeroclube criado!')
      }
      reset(); load()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Erro') }
  }

  const openEdit = (a: any) => { setNome(a.nome); setEditingId(a.id) }

  const handleDelete = async (id: number, nome_acro: string) => {
    if (!confirm(`Excluir aeroclube "${nome_acro}"?`)) return
    try { await AeroclubesAPI.excluir(id); toast.success('Aeroclube excluído!'); load() }
    catch (err: any) { toast.error(err.response?.data?.detail || 'Erro ao excluir') }
  }

  return (
    <Layout title="Aeroclubes">
      <div className="flex justify-between items-center mb-6">
        <p className="text-gray-500">{aeroclubes.length} aeroclube(s)</p>
        {isProprietario && (
          <select value={filtroAeroclube} onChange={(e) => setFiltroAeroclube(e.target.value)}
            className="px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100 text-sm">
            <option value="">Todos os Aeroclubes</option>
            {aeroclubes.map((a: any) => <option key={a.id} value={a.id}>{a.nome}</option>)}
          </select>
        )}
      </div>

      <form onSubmit={handleSubmit} className="bg-dark-800 border border-dark-700 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">{editingId ? 'Editar Aeroclube' : 'Novo Aeroclube'}</h3>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-400 mb-1">Nome</label>
            <input value={nome} onChange={(e) => setNome(e.target.value)}
              className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
          </div>
          <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            {editingId ? 'Atualizar' : 'Salvar'}
          </button>
          {editingId && (
            <button type="button" onClick={reset} className="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600 transition">
              Cancelar
            </button>
          )}
        </div>
      </form>

      <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">ID</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Nome</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Topic Write</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Topic Read</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {aeroclubes.filter((a) => !filtroAeroclube || a.id === Number(filtroAeroclube)).map((a: any) => (
              <tr key={a.id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 text-gray-400">{a.id}</td>
                <td className="px-4 py-3 font-medium text-gray-200">{a.nome}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-400">{a.topic_write || '-'}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-400">{a.topic_read || '-'}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(a)} className="text-blue-400 hover:text-blue-300 text-sm">Editar</button>
                    <button onClick={() => handleDelete(a.id, a.nome)} className="text-red-400 hover:text-red-300 text-sm">Excluir</button>
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
