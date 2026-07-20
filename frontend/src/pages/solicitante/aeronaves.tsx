import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { AeronavesAPI } from '@/services/api'

export default function SolicitanteAeronaves() {
  const [aeronaves, setAeronaves] = useState<any[]>([])

  const load = () => AeronavesAPI.listar().then(setAeronaves).catch(() => {})
  useEffect(() => { load() }, [])

  return (
    <Layout title="Minhas Aeronaves">
      <div className="flex justify-between items-center mb-6">
        <p className="text-gray-500">{aeronaves.length} aeronave(s)</p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Matrícula</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Modelo</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Fabricante</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-400">Tipo</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-400">Peso Máx</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {aeronaves.map((a: any) => (
              <tr key={a.id} className="hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-gray-200">{a.matricula}</td>
                <td className="px-4 py-3 text-gray-300">{a.modelo}</td>
                <td className="px-4 py-3 text-gray-300">{a.fabricante || '-'}</td>
                <td className="px-4 py-3 text-gray-300">{a.tipo || '-'}</td>
                <td className="px-4 py-3 text-right text-gray-300">{a.peso_maximo ? `${a.peso_maximo} kg` : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
