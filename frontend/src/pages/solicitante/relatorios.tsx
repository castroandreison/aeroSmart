import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { UsuariosAPI } from '@/services/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export default function SolicitanteRelatorios() {
  const [userNome, setUserNome] = useState('')
  const [periodo, setPeriodo] = useState({ inicio: '', fim: '' })

  useEffect(() => {
    UsuariosAPI.me().then((u) => setUserNome(u.nome_completo)).catch(() => {})
  }, [])

  const getToken = () => localStorage.getItem('token')

  return (
    <Layout title="Meus Relatórios">
      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Relatório por Período</h3>
        <div className="flex gap-4 mb-4 flex-wrap">
          <input type="date" value={periodo.inicio} onChange={(e) => setPeriodo({ ...periodo, inicio: e.target.value })}
            className="px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" />
          <input type="date" value={periodo.fim} onChange={(e) => setPeriodo({ ...periodo, fim: e.target.value })}
            className="px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100" />
          <button
            onClick={() => window.open(`${API_URL}/relatorios/usuarios/pdf?usuario_nome=${encodeURIComponent(userNome)}&data_inicio=${periodo.inicio}&data_fim=${periodo.fim}&token=${getToken()}`, '_blank')}
            disabled={!periodo.inicio || !periodo.fim}
            className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition disabled:opacity-50 shadow-lg shadow-red-600/20">
            Download PDF
          </button>
        </div>
      </div>
    </Layout>
  )
}
