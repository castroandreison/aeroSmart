import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const LoginAPI = {
  login: (email: string, senha: string) =>
    api.post('/auth/login', { email, senha }).then((r) => r.data),
}

export const UsuariosAPI = {
  listar: (params?: any) => api.get('/usuarios', { params }).then((r) => r.data),
  obter: (id: number) => api.get(`/usuarios/${id}`).then((r) => r.data),
  criar: (data: any) => api.post('/usuarios', data).then((r) => r.data),
  atualizar: (id: number, data: any) => api.put(`/usuarios/${id}`, data).then((r) => r.data),
  excluir: (id: number) => api.delete(`/usuarios/${id}`).then((r) => r.data),
  ativarInativar: (id: number) => api.put(`/usuarios/${id}/ativar-inativar`).then((r) => r.data),
  alterarSenha: (data: any) => api.post('/usuarios/alterar-senha', data).then((r) => r.data),
  me: () => api.get('/usuarios/me/perfil').then((r) => r.data),
  listarAeroclubes: () => api.get('/usuarios/aeroclubes/lista').then((r) => r.data),
}

export const AeronavesAPI = {
  listar: (params?: any) => api.get('/aeronaves', { params }).then((r) => r.data),
  obter: (id: number) => api.get(`/aeronaves/${id}`).then((r) => r.data),
  criar: (data: any) => api.post('/aeronaves', data).then((r) => r.data),
  atualizar: (id: number, data: any) => api.put(`/aeronaves/${id}`, data).then((r) => r.data),
  excluir: (id: number) => api.delete(`/aeronaves/${id}`).then((r) => r.data),
}

export const AgendamentosAPI = {
  listar: (incluirFinalizados?: boolean) => api.get('/agendamentos', { params: { incluir_finalizados: incluirFinalizados } }).then((r) => r.data),
  obter: (id: number) => api.get(`/agendamentos/${id}`).then((r) => r.data),
  criar: (data: any) => api.post('/agendamentos', data).then((r) => r.data),
  atualizar: (id: number, data: any) => api.put(`/agendamentos/${id}`, data).then((r) => r.data),
  cancelar: (id: number) => api.delete(`/agendamentos/${id}`).then((r) => r.data),
}

export const ConfiguracoesAPI = {
  listar: () => api.get('/configuracoes').then((r) => r.data),
  atualizar: (chave: string, data: any) => api.put(`/configuracoes/${chave}`, data).then((r) => r.data),
  inicializar: () => api.post('/configuracoes/inicializar').then((r) => r.data),
}

export const FinanceiroAPI = {
  listar: () => api.get('/financeiro').then((r) => r.data),
  resumo: (dataInicio: string, dataFim: string) =>
    api.get('/financeiro/resumo', { params: { data_inicio: dataInicio, data_fim: dataFim } }).then((r) => r.data),
  calcularCustos: (tempoMinutos: number) =>
    api.get('/financeiro/calcular-custos', { params: { tempo_minutos: tempoMinutos } }).then((r) => r.data),
  gerarDadosTeste: () => api.post('/financeiro/gerar-dados-teste').then((r) => r.data),
  apagarDados: () => api.delete('/financeiro/dados').then((r) => r.data),
}

export const MonitoramentoAPI = {
  statusPista: () => api.get('/monitoramento/status-pista').then((r) => r.data),
  dashboardAdmin: () => api.get('/monitoramento/dashboard-admin').then((r) => r.data),
  dashboardSolicitante: () => api.get('/monitoramento/dashboard-solicitante').then((r) => r.data),
  dashboardProprietario: () => api.get('/monitoramento/dashboard-proprietario').then((r) => r.data),
  cameraStatus: () => api.get('/monitoramento/camera/status').then((r) => r.data),
  cameraSnapshot: () => api.get('/monitoramento/camera/snapshot').then((r) => r.data),
  streamStatus: () => `${API_URL}/monitoramento/stream`,
  heartbeat: () => api.get('/monitoramento/heartbeat').then((r) => r.data),
}

export const LogsAPI = {
  listar: (params?: any) => api.get('/logs', { params }).then((r) => r.data),
}

export const AutomacaoAPI = {
  status: () => api.get('/automacao/status').then((r) => r.data),
  testarLigamento: (id: number) => api.post(`/automacao/testar-ligamento/${id}`).then((r) => r.data),
  testarDesligamento: (id: number) => api.post(`/automacao/testar-desligamento/${id}`).then((r) => r.data),
  listarControladores: () => api.get('/automacao/controladores').then((r) => r.data),
  criarControlador: (data: any) => api.post('/automacao/controladores', data).then((r) => r.data),
}

export const AeroclubesAPI = {
  listar: () => api.get('/aeroclubes').then((r) => r.data),
  obter: (id: number) => api.get(`/aeroclubes/${id}`).then((r) => r.data),
  criar: (data: any) => api.post('/aeroclubes', data).then((r) => r.data),
  atualizar: (id: number, data: any) => api.put(`/aeroclubes/${id}`, data).then((r) => r.data),
  excluir: (id: number) => api.delete(`/aeroclubes/${id}`).then((r) => r.data),
}

export const MqttAPI = {
  config: () => api.get('/mqtt/config').then((r) => r.data),
  salvarConfig: (data: any) => api.put('/mqtt/config', data).then((r) => r.data),
  status: () => api.get('/mqtt/status').then((r) => r.data),
  testar: () => api.post('/mqtt/testar').then((r) => r.data),
  testarComando: (data: any) => api.post('/mqtt/testar-comando', data).then((r) => r.data),
  alertas: () => api.get('/mqtt/alertas').then((r) => r.data),
  marcarLido: (id: number) => api.put(`/mqtt/alertas/${id}/ler`).then((r) => r.data),
  lerEnergia: (data: any) => api.post('/mqtt/ler-energia', data).then((r) => r.data),
}

export const RelatoriosAPI = {
  financeiro: (dataInicio: string, dataFim: string, formato?: string) =>
    api.get('/relatorios/financeiro', { params: { data_inicio: dataInicio, data_fim: dataFim, formato } }).then((r) => r.data),
  energia: (dataInicio: string, dataFim: string, formato?: string) =>
    api.get('/relatorios/energia', { params: { data_inicio: dataInicio, data_fim: dataFim, formato } }).then((r) => r.data),
  usuario: (usuarioId: number, dataInicio: string, dataFim: string, formato?: string) =>
    api.get(`/relatorios/usuarios/${usuarioId}`, { params: { data_inicio: dataInicio, data_fim: dataFim, formato } }).then((r) => r.data),
  mensal: (ano: number, mes: number, formato?: string) =>
    api.get('/relatorios/mensal', { params: { ano, mes, formato } }).then((r) => r.data),
}
