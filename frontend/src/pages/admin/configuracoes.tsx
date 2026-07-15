import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { ConfiguracoesAPI } from '@/services/api'
import toast from 'react-hot-toast'

const PRICING_KEYS = [
  'valor_acionamento',
  'valor_kwh',
  'potencia_instalada_kw',
  'tempo_minimo_cobranca_min',
  'tempo_adicional_min',
  'impostos_percentual',
  'taxas_extras',
]

export default function AdminConfiguracoes() {
  const [configs, setConfigs] = useState<any[]>([])

  const load = () =>
    ConfiguracoesAPI.listar()
      .then((all) => setConfigs(all.filter((c: any) => PRICING_KEYS.includes(c.chave))))
      .catch(() => {})
  useEffect(() => { load() }, [])

  const update = async (chave: string, valor: string) => {
    try { await ConfiguracoesAPI.atualizar(chave, { valor }); toast.success('Atualizado!'); load() }
    catch { toast.error('Erro') }
  }

  return (
    <Layout title="Configurações">
      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-sm p-6">
        <div className="space-y-1">
          {configs.map((c: any) => (
            <div key={c.chave} className="flex items-center justify-between py-4 border-b border-dark-700 last:border-0">
              <div>
                <p className="font-medium text-gray-200">{c.chave}</p>
                <p className="text-sm text-gray-500">{c.descricao}</p>
              </div>
              <div className="flex items-center gap-2">
                {c.tipo === 'booleano' ? (
                  <input
                    type="checkbox"
                    defaultChecked={c.valor === 'true'}
                    className="w-5 h-5 rounded bg-dark-800 border-dark-600 text-neon-500 focus:ring-neon-500"
                    onChange={(e) => update(c.chave, String(e.target.checked))}
                  />
                ) : (
                  <input
                    type={c.tipo === 'decimal' || c.tipo === 'int' ? 'number' : 'text'}
                    defaultValue={c.valor}
                    className="px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg w-48 text-right text-gray-100"
                    step={c.tipo === 'decimal' ? '0.01' : '1'}
                    onBlur={(e) => update(c.chave, e.target.value)}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
