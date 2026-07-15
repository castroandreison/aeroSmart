import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { LogsAPI } from '@/services/api'

export default function AdminLogs() {
  const [logs, setLogs] = useState<any[]>([])

  useEffect(() => { LogsAPI.listar({ limit: 200 }).then(setLogs).catch(() => {}) }, [])

  return (
    <Layout title="Logs de Auditoria">
      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-800">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Data/Hora</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Usuário</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Ação</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Entidade</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Descrição</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {logs.map((log: any) => (
              <tr key={log.id} className="hover:bg-dark-800/50">
                <td className="px-4 py-2 text-sm text-gray-400">
                  {log.created_at ? new Date(log.created_at).toLocaleString('pt-BR') : '-'}
                </td>
                <td className="px-4 py-2 text-sm text-gray-300">{log.usuario_nome || '-'}</td>
                <td className="px-4 py-2">
                  <span className="px-2 py-1 rounded-full text-xs bg-dark-700 text-gray-300">{log.acao}</span>
                </td>
                <td className="px-4 py-2 text-sm text-gray-400">{log.entidade ? `${log.entidade}#${log.entidade_id}` : '-'}</td>
                <td className="px-4 py-2 text-sm text-gray-500">{log.descricao || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
