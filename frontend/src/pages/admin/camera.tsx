import { useState } from 'react'
import Layout from '@/components/Layout'
import { MonitoramentoAPI } from '@/services/api'

export default function AdminCamera() {
  const [snapshot, setSnapshot] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const getSnapshot = async () => {
    setLoading(true)
    try {
      const data = await MonitoramentoAPI.cameraSnapshot()
      setSnapshot(`data:${data.formato};base64,${data.snapshot}`)
    } catch { alert('Câmera indisponível') }
    setLoading(false)
  }

  return (
    <Layout title="Monitoramento por Câmera">
      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
        <div className="mb-4">
          {snapshot ? (
            <img src={snapshot} alt="Pista" className="w-full rounded-lg border border-dark-600" />
          ) : (
            <div className="w-full h-64 bg-dark-800 border border-dark-700 rounded-lg flex items-center justify-center text-gray-600">
              Clique em "Tirar Snapshot" para visualizar
            </div>
          )}
        </div>
        <button
          onClick={getSnapshot}
          disabled={loading}
          className="px-6 py-3 bg-neon-600 hover:bg-neon-500 text-white rounded-lg transition disabled:opacity-50 shadow-lg shadow-neon-600/20"
        >
          {loading ? 'Capturando...' : 'Tirar Snapshot'}
        </button>
      </div>
    </Layout>
  )
}
