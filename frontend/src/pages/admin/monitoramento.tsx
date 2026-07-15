import { useEffect, useState, useRef } from 'react'
import Layout from '@/components/Layout'
import { MonitoramentoAPI } from '@/services/api'

export default function AdminMonitoramento() {
  const [pista, setPista] = useState<any>(null)
  const [cameraOnline, setCameraOnline] = useState(false)
  const [snapshot, setSnapshot] = useState<string | null>(null)
  const es = useRef<EventSource | null>(null)

  useEffect(() => {
    MonitoramentoAPI.statusPista().then(setPista).catch(() => {})
    MonitoramentoAPI.cameraStatus().then((r) => setCameraOnline(r.online)).catch(() => {})

    const url = MonitoramentoAPI.streamStatus()
    es.current = new EventSource(url)
    es.current.onmessage = (event) => {
      try { setPista(JSON.parse(event.data)) } catch {}
    }
    return () => { es.current?.close() }
  }, [])

  const getSnapshot = async () => {
    try {
      const data = await MonitoramentoAPI.cameraSnapshot()
      setSnapshot(`data:${data.formato};base64,${data.snapshot}`)
    } catch {}
  }

  return (
    <Layout title="Monitoramento">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Status da Pista</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className={`w-6 h-6 rounded-full ${pista?.status === 'ligado' || pista?.status === 'ligando' ? 'bg-green-500 animate-pulse shadow-lg shadow-green-500/50' : 'bg-gray-600'}`} />
              <div>
                <p className="text-xl font-bold text-white capitalize">{pista?.status || 'Desconhecido'}</p>
                <p className="text-sm text-gray-500">
                  {pista?.status === 'ligado' ? 'Pista LIGADA' : 'Pista desligada'}
                </p>
              </div>
            </div>

            {pista?.tempo_ligado_segundos > 0 && (
              <div className="p-4 bg-neon-500/5 border border-neon-500/20 rounded-lg">
                <p className="text-sm text-gray-500">Tempo ligado</p>
                <p className="text-lg font-bold text-neon-400">{Math.round(pista.tempo_ligado_segundos / 60)} minutos</p>
              </div>
            )}

            {pista?.tempo_restante_segundos > 0 && (
              <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
                <p className="text-sm text-gray-500">Tempo restante</p>
                <p className="text-lg font-bold text-yellow-400">{Math.round(pista.tempo_restante_segundos / 60)} minutos</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Câmera</h3>
          <div className="flex items-center gap-2 mb-4">
            <div className={`w-3 h-3 rounded-full ${cameraOnline ? 'bg-green-500 shadow-lg shadow-green-500/50' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-400">{cameraOnline ? 'Online' : 'Offline'}</span>
          </div>

          {snapshot ? (
            <img src={snapshot} alt="Snapshot" className="w-full rounded-lg border border-dark-600" />
          ) : (
            <div className="w-full h-48 bg-dark-800 border border-dark-700 rounded-lg flex items-center justify-center text-gray-600">
              Snapshot não disponível
            </div>
          )}

          <button onClick={getSnapshot} className="mt-3 px-4 py-2 bg-neon-600 hover:bg-neon-500 text-white rounded-lg transition text-sm shadow-lg shadow-neon-600/20">
            Tirar Snapshot
          </button>
        </div>
      </div>
    </Layout>
  )
}
