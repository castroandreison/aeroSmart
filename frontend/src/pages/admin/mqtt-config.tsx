import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { api } from '@/services/api'
import { AeroclubesAPI } from '@/services/api'
import toast from 'react-hot-toast'
import { Eye, EyeOff } from 'lucide-react'

export default function MqttConfig() {
  const [config, setConfig] = useState({ host: '', port: 1883, username: '', password: '', topic_prefix: 'aeroclube', timeout: 10 })
  const [alertas, setAlertas] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [logExpandido, setLogExpandido] = useState<Set<number>>(new Set())
  const [connected, setConnected] = useState(false)
  const [aeroclubes, setAeroclubes] = useState<any[]>([])
  const [testeAeroclubeId, setTesteAeroclubeId] = useState('')
  const [testeComando, setTesteComando] = useState('BalOn')
  const [testando, setTestando] = useState(false)

  const load = () => {
    api.get('/mqtt/config').then((r) => setConfig({ ...config, ...r.data })).catch(() => {})
    api.get('/mqtt/status').then((r) => setConnected(r.data.connected)).catch(() => {})
    api.get('/mqtt/alertas').then((r) => setAlertas(r.data)).catch(() => {})
    api.get('/mqtt/logs').then((r) => setLogs(r.data)).catch(() => {})
    AeroclubesAPI.listar().then(setAeroclubes).catch(() => {})
  }
  useEffect(() => { load() }, [])

  const salvar = async (e: any) => {
    e.preventDefault()
    try {
      await api.put('/mqtt/config', config)
      toast.success('Configuração salva!')
    } catch { toast.error('Erro ao salvar') }
  }

  const testarConexao = async () => {
    try {
      const r = await api.post('/mqtt/testar')
      setConnected(true)
      toast.success(r.data.message)
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Falha na conexão') }
  }

  const testarComando = async () => {
    if (!testeAeroclubeId) { toast.error('Selecione um aeroclube'); return }
    setTestando(true)
    try {
      const ac = aeroclubes.find((a: any) => a.id === Number(testeAeroclubeId))
      const r = await api.post('/mqtt/testar-comando', {
        comando: testeComando,
        aeroclube_id: Number(testeAeroclubeId),
        aeroclube_nome: ac?.nome || 'Teste',
      })
      if (testeComando === 'Heartbeat') {
        toast.success(r.data.confirmado ? 'Heartbeat recebido!' : 'Heartbeat sem resposta')
      } else {
        toast.success(r.data.confirmado ? 'Comando confirmado!' : 'Comando enviado sem confirmação')
      }
      load()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Erro') }
    setTestando(false)
  }

  const marcarLido = async (id: number) => {
    try { await api.put(`/mqtt/alertas/${id}/ler`); load() }
    catch { toast.error('Erro') }
  }

  return (
    <Layout title="Configuração MQTT">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Config */}
        <form onSubmit={salvar} className="bg-dark-800 border border-dark-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-100 mb-4">Broker MQTT</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Host</label>
              <input value={config.host} onChange={(e) => setConfig({ ...config, host: e.target.value })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Porta</label>
              <input type="number" value={config.port} onChange={(e) => setConfig({ ...config, port: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Usuário</label>
              <input value={config.username} onChange={(e) => setConfig({ ...config, username: e.target.value })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Senha</label>
              <input type="password" value={config.password} onChange={(e) => setConfig({ ...config, password: e.target.value })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Prefixo dos Tópicos</label>
              <input value={config.topic_prefix} onChange={(e) => setConfig({ ...config, topic_prefix: e.target.value })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Timeout (segundos)</label>
              <input type="number" value={config.timeout} onChange={(e) => setConfig({ ...config, timeout: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100" />
            </div>
            <div className="flex gap-3">
              <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                Salvar
              </button>
              <button type="button" onClick={testarConexao}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
                Testar Conexão
              </button>
            </div>
            <div className={`text-sm ${connected ? 'text-green-400' : 'text-red-400'}`}>
              Status: {connected ? 'Conectado' : 'Desconectado'}
            </div>
          </div>
        </form>

        {/* Testar Comando */}
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-100 mb-4">Testar Comando</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Aeroclube</label>
              <select value={testeAeroclubeId} onChange={(e) => setTesteAeroclubeId(e.target.value)}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100">
                <option value="">Selecione...</option>
                {aeroclubes.map((a: any) => <option key={a.id} value={a.id}>{a.nome}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Comando</label>
              <select value={testeComando} onChange={(e) => setTesteComando(e.target.value)}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-gray-100">
                <option value="BalOn">BalOn (Ligar)</option>
                <option value="BalOff">BalOff (Desligar)</option>
                <option value="Heartbeat">Heartbeat</option>
              </select>
            </div>
            <button type="button" onClick={testarComando} disabled={testando}
              className="px-6 py-2 bg-neon-600 hover:bg-neon-500 disabled:bg-dark-600 disabled:cursor-not-allowed text-white rounded-lg transition">
              {testando ? 'Enviando...' : 'Enviar Comando'}
            </button>
          </div>
        </div>
      </div>

      {/* Alertas */}
      <div className="mt-6 bg-dark-800 border border-dark-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">Alertas de Balizador</h3>
        {alertas.length === 0 ? (
          <p className="text-gray-500 text-sm">Nenhum alerta registrado</p>
        ) : (
          <div className="space-y-3">
            {alertas.map((a: any) => (
              <div key={a.id} className="p-4 rounded-lg border bg-red-900/20 border-red-700/50">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-red-300">{a.estacao}</p>
                    <p className="text-sm text-gray-400 mt-1">{a.mensagem}</p>
                    <p className="text-xs text-gray-500 mt-1">{a.created_at}</p>
                  </div>
                  <button onClick={() => marcarLido(a.id)}
                    className="px-3 py-1 text-xs bg-red-700 text-white rounded hover:bg-red-600 transition">
                    Apagar
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Log de Comandos */}
      <div className="mt-6 bg-dark-800 border border-dark-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">Log de Comandos</h3>
        {logs.length === 0 ? (
          <p className="text-gray-500 text-sm">Nenhum comando enviado ainda</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-dark-700">
                  <th className="text-left py-2 px-3">Data/Hora</th>
                  <th className="text-left py-2 px-3">Tópico</th>
                  <th className="text-left py-2 px-3">Payload</th>
                  <th className="text-center py-2 px-3">Status</th>
                  <th className="text-left py-2 px-3">Detalhes</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l: any) => {
                  const det = l.detalhes || {}
                  const expandido = logExpandido.has(l.id)
                  return (
                    <tr key={l.id} className="border-b border-dark-700 hover:bg-dark-700/50">
                      <td className="py-2 px-3 text-gray-400 whitespace-nowrap font-mono text-xs">
                        {l.created_at ? new Date(l.created_at).toLocaleString('pt-BR') : '-'}
                      </td>
                      <td className="py-2 px-3 text-gray-200 font-mono text-xs">{det.topic || '-'}</td>
                      <td className="py-2 px-3">
                        {typeof det.payload === 'string' ? (
                          <span className={`font-mono text-xs px-2 py-0.5 rounded ${det.payload === 'BalOn' ? 'text-green-400 bg-green-900/30' : 'text-red-400 bg-red-900/30'}`}>
                            {det.payload}
                          </span>
                        ) : (
                          <span className="font-mono text-xs text-gray-300">
                            {JSON.stringify(det.payload)}
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {det.confirmado ? (
                          <span className="text-green-400 text-xs">✓ Confirmado</span>
                        ) : (
                          <span className="text-yellow-400 text-xs">⚠ Enviado</span>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        <button
                          onClick={() => {
                            const next = new Set(logExpandido)
                            expandido ? next.delete(l.id) : next.add(l.id)
                            setLogExpandido(next)
                          }}
                          className="text-gray-500 hover:text-gray-300 transition flex items-center gap-1 text-xs"
                        >
                          {expandido ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                          {expandido ? 'Ocultar' : 'Ver'}
                        </button>
                        {expandido && (
                          <pre className="mt-2 p-2 bg-dark-950 border border-dark-600 rounded text-xs text-gray-300 font-mono overflow-x-auto max-h-40 overflow-y-auto">
                            {JSON.stringify(det, null, 2)}
                          </pre>
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
