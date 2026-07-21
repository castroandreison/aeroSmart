import { useEffect, useState, useRef } from 'react'
import Layout from '@/components/Layout'
import { MonitoramentoAPI, MqttAPI } from '@/services/api'
import { Calendar, Plane, DollarSign, Zap, Users, Clock, Activity, Wifi, WifiOff, AlertTriangle, CheckCircle, XCircle, Signal, Cpu, HardDrive, Settings } from 'lucide-react'

function formatHoras(dec: number): string {
  const h = Math.floor(dec)
  const m = Math.round((dec - h) * 60)
  if (h === 0) return `${m}min`
  if (m === 0) return `${h}h`
  return `${h}h ${m}min`
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}d ${h}h ${m}m`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function timeSince(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return 'agora'
  if (min < 60) return `${min}min atrás`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h}h atrás`
  return `${Math.floor(h / 24)}d atrás`
}

function WifiSignal({ quality }: { quality: number }) {
  const bars = quality >= 80 ? 4 : quality >= 60 ? 3 : quality >= 40 ? 2 : quality >= 20 ? 1 : 0
  const color = quality >= 60 ? 'text-green-400' : quality >= 40 ? 'text-yellow-400' : 'text-red-400'
  return (
    <div className={`flex items-center gap-1 ${color}`}>
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className={`w-1 rounded-full ${i <= bars ? 'bg-current' : 'bg-gray-600'}`} style={{ height: `${6 + i * 3}px` }} />
      ))}
      <span className="text-xs ml-1">{quality}%</span>
    </div>
  )
}

export default function AdminDashboard() {
  const [dashboard, setDashboard] = useState<any>(null)
  const [pista, setPista] = useState<any>(null)
  const [alertas, setAlertas] = useState<any[]>([])
  const [ultimosComandos, setUltimosComandos] = useState<any[]>([])
  const [mqttConnected, setMqttConnected] = useState<boolean | null>(null)
  const [heartbeats, setHeartbeats] = useState<Record<string, any>>({})
  const [lidos, setLidos] = useState<Set<number>>(new Set())
  const evtSource = useRef<EventSource | null>(null)

  useEffect(() => {
    MonitoramentoAPI.dashboardAdmin().then(setDashboard).catch(() => {})
    MonitoramentoAPI.statusPista().then(setPista).catch(() => {})
    MqttAPI.alertas().then(setAlertas).catch(() => {})
    MqttAPI.status().then((r) => setMqttConnected(r.connected)).catch(() => {})

    const url = MonitoramentoAPI.streamStatus()
    evtSource.current = new EventSource(url)
    evtSource.current.onmessage = (e) => {
      try { setPista(JSON.parse(e.data)) } catch {}
    }

    const fetchHeartbeat = async () => {
      try {
        const data = await MonitoramentoAPI.heartbeat()
        setHeartbeats(data)
      } catch {}
    }
    fetchHeartbeat()
    const hbInterval = setInterval(fetchHeartbeat, 10000)

    return () => {
      evtSource.current?.close()
      clearInterval(hbInterval)
    }
  }, [])

  const hbEntries = Object.entries(heartbeats)
  const isOnline = hbEntries.some(([_, hb]) => hb.timestamp && (Date.now() - new Date(hb.timestamp).getTime()) < 8 * 60 * 1000)

  const marcarLido = async (id: number) => {
    try {
      await MqttAPI.marcarLido(id)
      setLidos((prev) => new Set(prev).add(id))
    } catch {}
  }

  const cards = [
    { label: 'Agendamentos Hoje', value: dashboard?.agendamentos_dia ?? '...', icon: Calendar, color: 'bg-neon-500/10 text-neon-400' },
    { label: 'Agendamentos Futuros', value: dashboard?.agendamentos_futuros ?? '...', icon: Clock, color: 'bg-green-500/10 text-green-400' },
    { label: 'Concluídos', value: dashboard?.agendamentos_concluidos ?? '...', icon: Activity, color: 'bg-purple-500/10 text-purple-400' },
    { label: 'Usuários Cadastrados', value: dashboard?.usuarios_ativos ?? '...', icon: Users, color: 'bg-blue-500/10 text-blue-400' },
    { label: 'Horas de Utilização', value: dashboard?.horas_utilizacao != null ? formatHoras(dashboard.horas_utilizacao) : '...', icon: Plane, color: 'bg-orange-500/10 text-orange-400' },
    { label: 'Receita (mês)', value: `R$ ${dashboard?.receita?.toFixed(2) ?? '...'}`, icon: DollarSign, color: 'bg-green-500/10 text-green-400' },
    { label: 'Consumo (mês)', value: `${dashboard?.consumo_energia ?? '...'} kWh`, icon: Zap, color: 'bg-yellow-500/10 text-yellow-400' },
  ]

  return (
    <Layout title="Dashboard Administrativo">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <div key={card.label} className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6 hover:border-dark-600 transition">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{card.label}</p>
                  <p className="text-2xl font-bold mt-1 text-white">{card.value}</p>
                </div>
                <div className={`p-3 rounded-lg ${card.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Status do Balizador</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-4 h-4 rounded-full ${isOnline ? 'bg-green-500 shadow-lg shadow-green-500/50' : 'bg-red-500'}`} />
                <span className={`font-medium ${isOnline ? 'text-green-400' : 'text-red-400'}`}>{isOnline ? 'Online' : 'Offline'}</span>
              </div>
              <div className="flex items-center gap-2">
                {mqttConnected === true ? (
                  <span className="flex items-center gap-1 text-green-400 text-sm"><Wifi className="w-4 h-4" /> Comunicação</span>
                ) : mqttConnected === false ? (
                  <span className="flex items-center gap-1 text-red-400 text-sm"><WifiOff className="w-4 h-4" /> Comunicação</span>
                ) : null}
              </div>
            </div>
            {pista?.tempo_ligado_segundos > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <Activity className="w-4 h-4 text-neon-400" />
                <span className="text-gray-300">
                  Tempo ligado: {Math.floor(pista.tempo_ligado_segundos / 60)}min {Math.round(pista.tempo_ligado_segundos % 60)}s
                </span>
              </div>
            )}
            {pista?.tempo_restante_segundos > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="w-4 h-4 text-yellow-400" />
                <span className="text-gray-300">Tempo restante: {Math.round(pista.tempo_restante_segundos / 60)} min</span>
              </div>
            )}
            {pista?.comando_confirmado !== undefined && (
              <div className="flex items-center gap-2 text-sm">
                {pista.comando_confirmado ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                <span className={pista.comando_confirmado ? 'text-green-400' : 'text-red-400'}>
                  {pista.comando_confirmado ? 'Comando confirmado pelo ESP32' : 'Sem confirmação do ESP32'}
                </span>
              </div>
            )}
            {pista?.ultimo_comando && pista.status === 'desligado' && (
              <div className="flex items-center gap-2 text-sm">
                {pista.ultimo_confirmado ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                <span className="text-gray-400">
                  Último comando: {pista.ultimo_comando}
                  {pista.ultimo_confirmado ? ' (confirmado)' : ' (falha)'}
                </span>
              </div>
            )}
            {pista?.proximo_agendamento && (
              <p className="text-sm text-gray-500">
                Próximo: {new Date(pista.proximo_agendamento).toLocaleString('pt-BR')}
              </p>
            )}

            <hr className="border-dark-700 my-2" />

            {(hbEntries.length > 0 ? hbEntries : [['', {}]]).map(([name, hb]: [string, any]) => (
              <div key={name || 'placeholder'} className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-200">{hb.device?.nome || name || 'Aguardando...'}</span>
                  <span className="text-xs text-gray-500">
                    {hb.timestamp ? `${new Date(hb.timestamp).toLocaleString('pt-BR')} (${timeSince(hb.timestamp)})` : ''}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Signal className="w-4 h-4 text-gray-500" />
                    <WifiSignal quality={hb.wifi?.qualidade ?? 0} />
                  </div>
                  <div className="flex items-center gap-2">
                    {hb.mqtt?.status === 'Conectado' ? (
                      <span className="flex items-center gap-1 text-green-400"><Wifi className="w-4 h-4" /> Comunicação OK</span>
                    ) : (
                      <span className="flex items-center gap-1 text-gray-600"><Wifi className="w-4 h-4" /> Comunicação</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-300">{hb.sistema ? formatUptime(hb.sistema.uptime_segundos ?? 0) : '...'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-300" title={hb.firmware?.build_date || ''}>{hb.firmware?.versao ? `v${hb.firmware.versao}` : '...'}</span>
                  </div>
                </div>

                <div className="text-xs text-gray-500">
                  Build: {hb.firmware?.build_date || '...'}
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-dark-800 text-gray-400 border border-dark-600">
                    {hb.firmware?.ota_channel || '...'}
                  </span>
                </div>

                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>IP: {hb.wifi?.ip || '-'}</span>
                  <span>RSSI: {hb.wifi?.rssi ?? '-'} dBm</span>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm">
                    <div className={`w-2 h-2 rounded-full ${hb.balizamento?.status === 'Ativo' ? 'bg-green-500' : 'bg-gray-500'}`} />
                    <span className="text-gray-300">{hb.balizamento?.status === 'Ativo' ? 'Ativo' : 'Inativo'}</span>
                    <span className="text-gray-500 text-xs">
                      {hb.balizamento?.contador_acionamentos ?? 0} acionamentos
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {hb.balizamento?.modo_manual ? (
                      <>
                        <Settings className="w-4 h-4 text-yellow-400" />
                        <span className="text-yellow-400 font-medium">Manual</span>
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 text-neon-400" />
                        <span className="text-neon-400 font-medium">Automático</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Alertas do Balizador</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {alertas.length === 0 ? (
              <p className="text-sm text-gray-500">Nenhum alerta</p>
            ) : (
              alertas.filter((a: any) => !lidos.has(a.id)).slice(0, 10).map((a: any) => (
                <div key={a.id} className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-red-300 font-medium">{a.estacao}</p>
                    <p className="text-xs text-gray-400">{a.mensagem}</p>
                    <p className="text-xs text-gray-500 mt-1">{a.created_at ? new Date(a.created_at).toLocaleString('pt-BR') : ''}</p>
                  </div>
                  <button onClick={() => marcarLido(a.id)} className="px-3 py-1 text-xs bg-red-700 text-white rounded hover:bg-red-600 transition">
                    Lido
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Acesso Rápido</h3>
          <div className="grid grid-cols-2 gap-3">
            <a href="/admin/agendamentos" className="p-4 bg-neon-500/5 border border-neon-500/20 rounded-lg text-center hover:bg-neon-500/10 transition">
              <Calendar className="w-6 h-6 mx-auto text-neon-400" />
              <span className="text-sm mt-1 block text-gray-300">Agendamentos</span>
            </a>
            <a href="/admin/usuarios" className="p-4 bg-green-500/5 border border-green-500/20 rounded-lg text-center hover:bg-green-500/10 transition">
              <Users className="w-6 h-6 mx-auto text-green-400" />
              <span className="text-sm mt-1 block text-gray-300">Usuários</span>
            </a>
            <a href="/admin/financeiro" className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg text-center hover:bg-blue-500/10 transition">
              <DollarSign className="w-6 h-6 mx-auto text-blue-400" />
              <span className="text-sm mt-1 block text-gray-300">Financeiro</span>
            </a>
            <a href="/admin/monitoramento" className="p-4 bg-purple-500/5 border border-purple-500/20 rounded-lg text-center hover:bg-purple-500/10 transition">
              <Activity className="w-6 h-6 mx-auto text-purple-400" />
              <span className="text-sm mt-1 block text-gray-300">Monitoramento</span>
            </a>
          </div>
        </div>
      </div>
    </Layout>
  )
}