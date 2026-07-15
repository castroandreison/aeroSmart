import { useState, useEffect, useMemo } from 'react'
import Layout from '@/components/Layout'
import { AeroclubesAPI, UsuariosAPI } from '@/services/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export default function AdminRelatorios() {
  const [periodo, setPeriodo] = useState({ inicio: '', fim: '' })
  const [usuarios, setUsuarios] = useState<any[]>([])
  const [usuarioSelecionado, setUsuarioSelecionado] = useState<any>(null)
  const [busca, setBusca] = useState('')
  const [mostrarDropdown, setMostrarDropdown] = useState(false)
  const [mes, setMes] = useState({ ano: new Date().getFullYear(), mes: new Date().getMonth() + 1 })
  const [aeroclubes, setAeroclubes] = useState<any[]>([])
  const [aeroclube, setAeroclube] = useState('')

  useEffect(() => {
    AeroclubesAPI.listar().then(setAeroclubes).catch(() => {})
    UsuariosAPI.listar().then(setUsuarios).catch(() => {})
  }, [])

  const usuariosFiltrados = useMemo(() => {
    if (!busca) return usuarios
    const termo = busca.toLowerCase()
    return usuarios.filter((u: any) =>
      u.nome_completo?.toLowerCase().includes(termo) || u.email?.toLowerCase().includes(termo)
    )
  }, [busca, usuarios])

  useEffect(() => {
    const fechar = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('.user-search-wrap')) setMostrarDropdown(false)
    }
    document.addEventListener('mousedown', fechar)
    return () => document.removeEventListener('mousedown', fechar)
  }, [])

  const getToken = () => localStorage.getItem('token')

  const openPdf = (url: string) => window.open(url, '_blank')

  return (
    <Layout title="Relatórios">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Por Usuário</h3>
          <div className="space-y-3">
            <div className="relative user-search-wrap">
              <input type="text" value={busca} onChange={(e) => { setBusca(e.target.value); setMostrarDropdown(true); setUsuarioSelecionado(null) }}
                onFocus={() => setMostrarDropdown(true)}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" placeholder="Pesquisar usuário..." />
              {mostrarDropdown && usuariosFiltrados.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-dark-800 border border-dark-600 rounded-lg max-h-48 overflow-y-auto">
                  {usuariosFiltrados.map((u: any) => (
                    <button key={u.id} type="button"
                      onClick={() => { setUsuarioSelecionado(u); setBusca(u.nome_completo); setMostrarDropdown(false) }}
                      className="w-full text-left px-3 py-2 text-gray-100 hover:bg-dark-700 text-sm transition">
                      {u.nome_completo} <span className="text-gray-500 text-xs">({u.email})</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <input type="date" value={periodo.inicio} onChange={(e) => setPeriodo({ ...periodo, inicio: e.target.value })}
              className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" />
            <input type="date" value={periodo.fim} onChange={(e) => setPeriodo({ ...periodo, fim: e.target.value })}
              className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" />
            <button onClick={() => openPdf(`${API_URL}/relatorios/usuarios/pdf?usuario_nome=${encodeURIComponent(usuarioSelecionado?.nome_completo || busca)}&data_inicio=${periodo.inicio}&data_fim=${periodo.fim}&token=${getToken()}`)}
              disabled={!busca || !periodo.inicio || !periodo.fim}
              className="w-full py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition disabled:opacity-50 shadow-lg shadow-red-600/20">
              Download PDF
            </button>
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Relatório Mensal</h3>
          <div className="space-y-3">
            <select value={aeroclube} onChange={(e) => setAeroclube(e.target.value)}
              className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100">
              <option value="">Todos os Aeroclubes</option>
              {aeroclubes.map((a: any) => <option key={a.id} value={a.nome}>{a.nome}</option>)}
            </select>
            <div className="flex gap-3">
              <input type="number" value={mes.ano} onChange={(e) => setMes({ ...mes, ano: Number(e.target.value) })}
                className="w-1/2 px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" placeholder="Ano" />
              <input type="number" value={mes.mes} onChange={(e) => setMes({ ...mes, mes: Number(e.target.value) })}
                className="w-1/2 px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" placeholder="Mês" min={1} max={12} />
            </div>
            <button onClick={() => openPdf(`${API_URL}/relatorios/mensal/pdf?ano=${mes.ano}&mes=${mes.mes}&aeroclube=${aeroclube}&token=${getToken()}`)}
              className="w-full py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition shadow-lg shadow-red-600/20">
              Download PDF
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
