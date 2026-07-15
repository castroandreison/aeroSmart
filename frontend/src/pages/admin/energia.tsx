import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { api } from '@/services/api'
import { AeroclubesAPI } from '@/services/api'
import { Zap, Activity, Gauge, AlertTriangle, CheckCircle, WifiOff, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

const chipColors = [
  { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', icon: Gauge },
  { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20', icon: Activity },
  { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20', icon: Zap },
  { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20', icon: Activity },
  { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', icon: Activity },
  { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20', icon: Gauge },
  { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20', icon: Activity },
  { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', icon: Activity },
  { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', icon: Zap },
]

export default function Energia() {
  const [aeroclubes, setAeroclubes] = useState<any[]>([])
  const [testeAeroclubeId, setTesteAeroclubeId] = useState('')
  const [lendo, setLendo] = useState(false)
  const [dados, setDados] = useState<any>(null)
  const [ultimaLeitura, setUltimaLeitura] = useState<string | null>(null)
  const [logs, setLogs] = useState<any[]>([])
  const [logExpandido, setLogExpandido] = useState<Set<number>>(new Set())
  const [alertasEnergia, setAlertasEnergia] = useState<any[]>([])

  const load = () => {
    api.get('/mqtt/logs-energia').then((r) => setLogs(r.data)).catch(() => {})
    api.get('/mqtt/alertas-energia').then((r) => setAlertasEnergia(r.data)).catch(() => {})
    AeroclubesAPI.listar().then(setAeroclubes).catch(() => {})
  }

  useEffect(() => { load() }, [])

  const lerEnergia = async () => {
    if (!testeAeroclubeId) { toast.error('Selecione um aeroclube'); return }
    setLendo(true)
    try {
      const ac = aeroclubes.find((a: any) => a.id === Number(testeAeroclubeId))
      const r = await api.post('/mqtt/ler-energia', { aeroclube_nome: ac?.nome || 'AeroClub Central' })
      setDados(r.data)
      setUltimaLeitura(new Date().toLocaleString('pt-BR'))
      toast.success('Leitura concluída!')
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao ler medidor')
      load()
    }
    setLendo(false)
  }

  const marcarAlertaEnergiaLido = async (id: number) => {
    try { await api.put(`/mqtt/alertas/${id}/ler`); load() }
    catch { toast.error('Erro ao apagar alerta') }
  }

  const registradores = dados?.registradores ? Object.entries(dados.registradores) : []

  return (
    <Layout title="Medidor de Energia">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2 bg-dark-900 border border-dark-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-yellow-500/10 text-yellow-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Medidor de Energia</h3>
            </div>
          </div>
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-400 mb-1">Aeroclube</label>
              <select value={testeAeroclubeId} onChange={(e) => setTesteAeroclubeId(e.target.value)}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100">
                <option value="">Selecione...</option>
                {aeroclubes.map((a: any) => <option key={a.id} value={a.id}>{a.nome}</option>)}
              </select>
            </div>
            <button type="button" onClick={lerEnergia} disabled={lendo}
              className="px-6 py-2 bg-neon-600 hover:bg-neon-500 disabled:bg-dark-600 disabled:cursor-not-allowed text-white rounded-lg transition whitespace-nowrap flex items-center gap-2">
              {lendo ? (
                <>Lendo...</>
              ) : (
                <><Zap className="w-4 h-4" /> Ler Energia</>
              )}
            </button>
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Status da Leitura</h3>
          {dados ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-green-400 font-medium">{dados.status}</span>
              </div>
              {dados.equipamento && (
                <>
                  <p className="text-xs text-gray-500">
                    <span className="text-gray-400">Fabricante:</span> {dados.equipamento.fabricante}
                  </p>
                  <p className="text-xs text-gray-500">
                    <span className="text-gray-400">Modelo:</span> {dados.equipamento.modelo}
                  </p>
                  <p className="text-xs text-gray-500">
                    <span className="text-gray-400">Série:</span> {dados.equipamento.numero_serie}
                  </p>
                  <p className="text-xs text-gray-500">
                    <span className="text-gray-400">Firmware:</span> {dados.equipamento.firmware}
                  </p>
                </>
              )}
              {ultimaLeitura && (
                <p className="text-xs text-gray-500 pt-1 border-t border-dark-700">
                  <span className="text-gray-400">Última leitura:</span> {ultimaLeitura}
                </p>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <WifiOff className="w-4 h-4" />
              <span>Aguardando leitura</span>
            </div>
          )}
        </div>
      </div>

      {registradores.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {registradores.map(([key, reg]: [string, any], idx: number) => {
            const cc = chipColors[idx % chipColors.length]
            const Icon = cc.icon
            return (
              <div key={key} className={`bg-dark-900 border ${cc.border} rounded-xl p-5 hover:border-opacity-60 transition`}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-gray-500 font-mono">{key}</span>
                  <div className={`p-2 rounded-lg ${cc.bg} ${cc.text}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <p className="text-sm text-gray-400 mb-1">{reg.descricao}</p>
                <p className={`text-2xl font-bold ${cc.text}`}>
                  {reg.valor}
                  <span className="text-sm font-normal text-gray-500 ml-1">{reg.unidade}</span>
                </p>
              </div>
            )
          })}
        </div>
      )}

      {/* Alertas de Energia */}
      <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Alertas de Energia</h3>
        {alertasEnergia.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <WifiOff className="w-4 h-4" />
            <span>Nenhum alerta registrado</span>
          </div>
        ) : (
          <div className="space-y-3">
            {alertasEnergia.map((a: any) => (
              <div key={a.id} className={`p-4 rounded-lg border ${a.status === 'Concluído' ? 'bg-green-900/20 border-green-700/50' : 'bg-red-900/20 border-red-700/50'}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${a.status === 'Concluído' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                        {a.status}
                      </span>
                      <span className="text-sm text-gray-300">{a.estacao}</span>
                    </div>
                    <p className="text-xs text-gray-400">{a.mensagem}</p>
                    <p className="text-xs text-gray-500 mt-1">{a.created_at ? new Date(a.created_at).toLocaleString('pt-BR') : '-'}</p>
                  </div>
                  <button onClick={() => marcarAlertaEnergiaLido(a.id)}
                    className="px-3 py-1 text-xs bg-dark-700 text-gray-300 rounded hover:bg-dark-600 transition">
                    Apagar
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-dark-900 border border-dark-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Log de Comandos</h3>
        {logs.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <WifiOff className="w-4 h-4" />
            <span>Nenhum comando enviado ainda</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-dark-700">
                  <th className="text-left py-2 px-3">Data/Hora</th>
                  <th className="text-left py-2 px-3">Tópico</th>
                  <th className="text-left py-2 px-3">Comando</th>
                  <th className="text-center py-2 px-3">Status</th>
                  <th className="text-left py-2 px-3">Resposta</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l: any) => {
                  const det = l.detalhes || {}
                  const resp = det.resposta
                  const expandido = logExpandido.has(l.id)
                  return (
                    <tr key={l.id} className="border-b border-dark-700 hover:bg-dark-800/50">
                      <td className="py-2 px-3 text-gray-400 whitespace-nowrap font-mono text-xs">
                        {l.created_at ? new Date(l.created_at).toLocaleString('pt-BR') : '-'}
                      </td>
                      <td className="py-2 px-3 text-gray-200 font-mono text-xs">
                        {det.topic || '-'}
                      </td>
                      <td className="py-2 px-3">
                        <span className="font-mono text-xs text-gray-300">{det.payload || '-'}</span>
                      </td>
                      <td className="py-2 px-3 text-center">
                        {det.confirmado ? (
                          <span className="flex items-center justify-center gap-1 text-green-400 text-xs">
                            <CheckCircle className="w-3 h-3" /> Confirmado
                          </span>
                        ) : (
                          <span className="flex items-center justify-center gap-1 text-yellow-400 text-xs">
                            <AlertTriangle className="w-3 h-3" /> Enviado
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        {resp ? (
                          <div>
                            <div className="flex items-center gap-2 text-xs text-gray-400">
                              <span className={resp.status === 'OK' ? 'text-green-400' : 'text-yellow-400'}>{resp.status}</span>
                              <span className="text-gray-600">·</span>
                              <span>{resp.registradores ? Object.keys(resp.registradores).length : 0} registradores</span>
                              <button
                                onClick={() => {
                                  const next = new Set(logExpandido)
                                  expandido ? next.delete(l.id) : next.add(l.id)
                                  setLogExpandido(next)
                                }}
                                className="text-gray-500 hover:text-gray-300 transition ml-1"
                              >
                                {expandido ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                              </button>
                            </div>
                            {expandido && (
                              <pre className="mt-1 p-2 bg-dark-950 border border-dark-600 rounded text-xs text-gray-300 font-mono overflow-x-auto max-h-40 overflow-y-auto">
                                {JSON.stringify(resp, null, 2)}
                              </pre>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-600">-</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}

