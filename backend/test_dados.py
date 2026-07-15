import urllib.request, json

BASE = "http://127.0.0.1:8000/api/v1"

def req(url, token=None, data=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=10)
    return json.loads(r.read())

# Admin login
admin = req(f"{BASE}/auth/login", data={"email": "admin@aeroclub.com", "senha": "admin123"})
token = admin["access_token"]
print("=== Admin Dashboard ===")
print(json.dumps(req(f"{BASE}/monitoramento/dashboard-admin", token), indent=2))

print("\n=== Relatório Financeiro (Jan-Jun 2026) ===")
print(json.dumps(req(f"{BASE}/relatorios/financeiro?data_inicio=2026-01-01&data_fim=2026-07-31", token), indent=2))

print("\n=== Agendamentos ===")
ags = req(f"{BASE}/agendamentos/", token)
print(f"Total: {len(ags)}")
for a in ags:
    dt = a["data"][:10]
    print(f"  {dt} | {a['solicitante_nome']:20s} | {a['aeronave_matricula']:8s} | {a['status']}")

print("\n=== Financeiro (últimos 5) ===")
fin = req(f"{BASE}/financeiro/", token)
for f in fin[:5]:
    print(f"  Agendamento #{f['agendamento_id']} | R$ {f['valor_total']:.2f} | {f['energia_consumida_kwh']:.2f} kWh")

print("\n=== Usuários ===")
users = req(f"{BASE}/usuarios/", token)
for u in users:
    print(f"  {u['id']}: {u['nome_completo']} ({u['email']}) - {u['nivel_acesso']}")

print("\n=== Usuário andreison ===")
user = req(f"{BASE}/auth/login", data={"email": "andreison.castro@email.com", "senha": "castro"})
t2 = user["access_token"]
print(json.dumps(req(f"{BASE}/monitoramento/dashboard-solicitante", t2), indent=2))
