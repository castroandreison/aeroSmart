import { useEffect, useState, useRef } from 'react'
import Layout from '@/components/Layout'
import { MonitoramentoAPI, MqttAPI } from '@/services/api'
import { Calendar, Plane, DollarSign, Zap, Users, Clock, Activity, Wifi, WifiOff, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

export default function AdminDashboard() {
  const [dashboard, setDashboard] = useState<any>(null)
  const [pista, setPista] = useState<any>(null)
  const [alertas, setAlertas] = useState<any[]>([])
  const [ultimosComandos, setUltimosComandos] = useState<any[]>([])
  const [mqttConnected, setMqttConnected] = useState<boolean | null>(null)
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
    return () => evtSource.current?.close()
  }, [])

  const cards = [
    { label: 'Agendamentos Hoje', value: dashboard?.agendamentos_dia ?? '...', icon: Calendar, color: 'bg-neon-500/10 text-neon-400' },
    { label: 'Agendamentos Futuros', value: dashboard?.agendamentos_futuros ?? '...', icon: Clock, color: 'bg-green-500/10 text-green-400' },
    { label: 'Concluídos', value: dashboard?.agendamentos_concluidos ?? '...', icon: Activity, color: 'bg-purple-500/10 text-purple-400' },
    { label: 'Horas de Utilização', value: `${dashboard?.horas_utilizacao ?? '...'}h`, icon: Plane, color: 'bg-orange-500/10 text-orange-400' },
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
                <div className={`w-4 h-4 rounded-full ${pista?.status === 'ligado' ? 'bg-green-500 shadow-lg shadow-green-500/50 animate-pulse' : pista?.status === 'ligando' ? 'bg-yellow-500 shadow-lg shadow-yellow-500/50 animate-pulse' : 'bg-gray-600'}`} />
                <span className="font-medium text-gray-200 capitalize">{pista?.status || 'Desconhecido'}</span>
              </div>
              <div className="flex items-center gap-2">
                {mqttConnected === true ? (
                  <span className="flex items-center gap-1 text-green-400 text-sm"><Wifi className="w-4 h-4" /> MQTT</span>
                ) : mqttConnected === false ? (
                  <span className="flex items-center gap-1 text-red-400 text-sm"><WifiOff className="w-4 h-4" /> MQTT</span>
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
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Alertas do Balizador</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {alertas.length === 0 ? (
              <p className="text-sm text-gray-500">Nenhum alerta</p>
            ) : (
              alertas.slice(0, 10).map((a: any) => (
                <div key={a.id} className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-red-300 font-medium">{a.estacao}</p>
                    <p className="text-xs text-gray-400">{a.mensagem}</p>
                    <p className="text-xs text-gray-500 mt-1">{a.created_at ? new Date(a.created_at).toLocaleString('pt-BR') : ''}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Sinal de Recebimento / Acionamento</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-4 p-4 bg-dark-800 rounded-lg">
              <div className={`p-3 rounded-full ${mqttConnected ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                {mqttConnected ? (
                  <CheckCircle className="w-8 h-8 text-green-400" />
                ) : (
                  <XCircle className="w-8 h-8 text-red-400" />
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-200">
                  {mqttConnected ? 'Broker MQTT conectado' : 'Broker MQTT desconectado'}
                </p>
                <p className="text-xs text-gray-500">
                  {pista?.status === 'ligado'
                    ? 'Comando recebido pelo balizador'
                    : pista?.status === 'ligando'
                    ? 'Aguardando confirmação do balizador...'
                    : pista?.ultimo_confirmado === true
                    ? 'Último comando foi confirmado'
                    : pista?.ultimo_confirmado === false
                    ? 'Último comando falhou - verifique alertas'
                    : 'Nenhum comando enviado'}
                </p>
              </div>
            </div>
            {pista?.comando_confirmado !== undefined && (
              <div className={`flex items-center gap-3 p-3 rounded-lg border text-sm ${pista.comando_confirmado ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
                {pista.comando_confirmado ? (
                  <CheckCircle className="w-5 h-5 text-green-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400" />
                )}
                <span className={pista.comando_confirmado ? 'text-green-300' : 'text-red-300'}>
                  {pista.comando_confirmado
                    ? 'Balizador acionado - sinal OK'
                    : 'Balizador sem resposta'}
                </span>
              </div>
            )}
          </div>
        </div>

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
            <a href="/admin/mqtt-config" className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg text-center hover:bg-blue-500/10 transition">
              <Wifi className="w-6 h-6 mx-auto text-blue-400" />
              <span className="text-sm mt-1 block text-gray-300">MQTT Config</span>
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