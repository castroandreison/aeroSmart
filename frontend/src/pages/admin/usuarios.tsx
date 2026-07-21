import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { useAuth } from '@/contexts/AuthContext'
import { UsuariosAPI, AeroclubesAPI, AeronavesAPI } from '@/services/api'
import toast from 'react-hot-toast'

const emptyForm = { nome_completo: '', email: '', cpf: '', senha: '', whatsapp: '', aeroclube_id: '', nivel_acesso: 'solicitante', observacoes: '', aeronave_id: '' }

export default function AdminUsuarios() {
  const { user } = useAuth()
  const isProprietario = user?.nivel_acesso === 'proprietario'
  const isAdmin = user?.nivel_acesso === 'administrador'
  const [usuarios, setUsuarios] = useState<any[]>([])
  const [aeroclubes, setAeroclubes] = useState<any[]>([])
  const [aeronaves, setAeronaves] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<any>({ ...emptyForm })
  const [filtroAeroclube, setFiltroAeroclube] = useState('')
  const [showSenha, setShowSenha] = useState(false)

  const load = (aeroclube?: string) => {
    const params: any = {}
    if (aeroclube) params.aeroclube_id = aeroclube
    UsuariosAPI.listar(params).then(setUsuarios).catch(() => {})
  }
  const loadAeroclubes = () => AeroclubesAPI.listar().then(setAeroclubes).catch(() => {})
  const loadAeronaves = () => AeronavesAPI.listar().then(setAeronaves).catch(() => {})
  useEffect(() => { load(); loadAeroclubes(); loadAeronaves() }, [])

  const resetForm = () => { setForm({ ...emptyForm }); setEditingId(null) }

  const openEdit = async (id: number) => {
    try {
      const u = await UsuariosAPI.obter(id)
      const userAero = aeronaves.find((a: any) => a.usuario_id === id)
      const aeroclube_id = isAdmin ? (user?.aeroclube_id ?? u.aeroclube_id ?? '') : (u.aeroclube_id ?? '')
      setForm({ ...emptyForm, ...u, senha: '', aeroclube_id, aeronave_id: userAero?.id ?? '' })
      setEditingId(id)
      setShowForm(true)
    } catch { toast.error('Erro ao carregar dados') }
  }

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    try {
      const payload: any = { ...form }
      const aeronave_id = payload.aeronave_id
      delete payload.aeronave_id; delete payload.id; delete payload.created_at; delete payload.updated_at; delete payload.ultimo_login; delete payload.senha_hash; delete payload.aeroclube
      if (!payload.senha) delete payload.senha
      payload.aeroclube_id = payload.aeroclube_id ? Number(payload.aeroclube_id) : null
      if (editingId) {
        await UsuariosAPI.atualizar(editingId, payload)
        if (aeronave_id) {
          await AeronavesAPI.atualizar(Number(aeronave_id), { usuario_id: editingId })
        }
        toast.success('Usuário atualizado!')
      } else {
        const novo = await UsuariosAPI.criar(payload)
        if (aeronave_id) {
          await AeronavesAPI.atualizar(Number(aeronave_id), { usuario_id: novo.id })
        }
        toast.success('Usuário criado!')
      }
      setShowForm(false)
      resetForm()
      load()
      loadAeronaves()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Erro') }
  }

  const toggleAtivo = async (id: number) => {
    try { await UsuariosAPI.ativarInativar(id); toast.success('Status alterado!'); load() }
    catch { toast.error('Erro') }
  }

  const handleDelete = async (id: number, nome: string) => {
    if (!confirm(`Excluir usuário "${nome}"? Esta ação não pode ser desfeita.`)) return
    try { await UsuariosAPI.excluir(id); toast.success('Usuário excluído!'); load() }
    catch (err: any) { toast.error(err.response?.data?.detail || 'Erro ao excluir') }
  }

  return (
    <Layout title="Usuários">
      <div className="flex justify-between items-center mb-6">
        <p className="text-gray-500">{usuarios.filter((u: any) => u.nivel_acesso === 'solicitante').length} usuários cadastrados</p>
        <div className="flex gap-3 items-center">
          {isProprietario && (
            <select value={filtroAeroclube} onChange={(e) => { setFiltroAeroclube(e.target.value); load(e.target.value) }}
              className="px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100 text-sm">
              <option value="">Todos os Aeroclubes</option>
              {aeroclubes.map((a: any) => <option key={a.id} value={a.id}>{a.nome}</option>)}
            </select>
          )}
          <button onClick={() => {
            if (!showForm) {
              resetForm()
              if (isAdmin && user?.aeroclube_id) setForm((f: any) => ({ ...f, aeroclube_id: user.aeroclube_id }))
            }
            setShowForm(!showForm)
          }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            {showForm ? 'Fechar' : 'Novo Usuário'}
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-dark-800 border border-dark-700 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-100 mb-4">{editingId ? 'Editar Usuário' : 'Novo Usuário'}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Nome *</label>
              <input value={form.nome_completo} onChange={(e) => setForm({ ...form, nome_completo: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Email *</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">CPF</label>
               <input value={form.cpf} onChange={(e) => setForm({ ...form, cpf: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div className="relative">
              <label className="block text-sm font-medium text-gray-400 mb-1">Senha {editingId && '(deixe em branco para manter)'}</label>
              <div className="relative">
                <input type={showSenha ? 'text' : 'password'} value={form.senha} onChange={(e) => setForm({ ...form, senha: e.target.value })} className="w-full px-3 py-2 pr-10 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
                <button type="button" onClick={() => setShowSenha(!showSenha)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200">
                  {showSenha ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-.69.069-1.365.2-2.015M6.343 6.343A7.98 7.98 0 0112 5c4.418 0 8 3.582 8 8 0 1.477-.401 2.86-1.1 4.05M6.343 6.343L3 3m3.343 3.343L21 21" /></svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                  )}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">WhatsApp</label>
              <input value={form.whatsapp} onChange={(e) => setForm({ ...form, whatsapp: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Aeroclube</label>
              {isAdmin && user?.aeroclube_id ? (
                <div className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-400 text-sm">
                  {aeroclubes.find((a: any) => a.id === Number(form.aeroclube_id))?.nome || 'Carregando...'}
                </div>
              ) : (
                <select value={form.aeroclube_id} onChange={(e) => setForm({ ...form, aeroclube_id: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100">
                  <option value="">Selecione...</option>
                  {aeroclubes.map((a: any) => <option key={a.id} value={a.id}>{a.nome}</option>)}
                </select>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Nível</label>
              <select value={form.nivel_acesso} onChange={(e) => setForm({ ...form, nivel_acesso: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100">
                {isProprietario ? (
                  <>
                    <option value="administrador">Administrador</option>
                    <option value="solicitante">Solicitante</option>
                    <option value="proprietario">Proprietário</option>
                  </>
                ) : (
                  <option value="solicitante">Solicitante</option>
                )}
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-400 mb-1">Observações</label>
              <textarea value={form.observacoes || ''} onChange={(e) => setForm({ ...form, observacoes: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" rows={2} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Aeronave (opcional)</label>
              <select value={form.aeronave_id} onChange={(e) => setForm({ ...form, aeronave_id: e.target.value })} className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100">
                <option value="">Nenhuma</option>
                {aeronaves.map((a: any) => (
                  <option key={a.id} value={a.id}>{a.matricula} - {a.modelo}{a.usuario_nome ? ` (${a.usuario_nome})` : ''}</option>
                ))}
              </select>
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
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Nome</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Email</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Aeroclube</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Matrícula</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Nível</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Status</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {usuarios.map((u: any) => (
              <tr key={u.id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-gray-200">{u.nome_completo}</td>
                <td className="px-4 py-3 text-gray-300">{u.email}</td>
                <td className="px-4 py-3 text-gray-300">{u.aeroclube || '-'}</td>
                <td className="px-4 py-3 text-gray-300">{u.matricula || '-'}</td>
                <td className="px-4 py-3 capitalize text-gray-300">{u.nivel_acesso}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${u.ativo ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                    {u.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(u.id)} className="text-blue-400 hover:text-blue-300 text-sm">Editar</button>
                    {user?.nivel_acesso === 'proprietario' && (
                      <button onClick={() => toggleAtivo(u.id)} className={`text-sm ${u.ativo ? 'text-yellow-400 hover:text-yellow-300' : 'text-green-400 hover:text-green-300'}`}>
                        {u.ativo ? 'Inativar' : 'Ativar'}
                      </button>
                    )}
                    {(user?.nivel_acesso === 'proprietario' || u.nivel_acesso === 'solicitante') && (
                      <button onClick={() => handleDelete(u.id, u.nome_completo)} className="text-red-400 hover:text-red-300 text-sm">Excluir</button>
                    )}
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
