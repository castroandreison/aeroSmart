# Documentação Técnica — Firmware Balizamento Pista (ESP32)

## 1. Identificação

| Item | Valor |
|---|---|
| Nome do dispositivo | `balizamento-pista` |
| Nome amigável | Balizamento Pista |
| Plataforma | ESP32 (ESP32Dev) via ESPHome + Arduino |
| Linguagem | C++ (ESPHome lambda + Arduino framework) |

## 2. Pinagem do ESP32

| GPIO | Nome | Direção | Pull | Descrição |
|---|---|---|---|---|
| 2 | `RELAY_PIN` | Output | — | Aciona o relé da pista. Inicializado LOW (desligado). |
| 4 | `MANUAL_PIN` | Input | `GPIO_PULLDOWN_ONLY` | Chave manual. HIGH = modo manual ativo. |
| 16 | `FLOW_CONTROL_PIN` | Output | — | Controle de fluxo RS485 (DE/RE). |
| 17 | `UART_TX` | Output | — | TX da RS485 para o medidor SDM120. |
| 18 | `UART_RX` | Input | — | RX da RS485 para o medidor SDM120. |

## 3. Conexões Externas

| Equipamento | Interface | Protocolo | Baudrate |
|---|---|---|---|
| Medidor Eastron SDM120 | RS485 (GPIO 17/18) | Modbus RTU | 9600 8N1 |
| Relé de potência | GPIO 2 | Digital (HIGH = liga) | — |
| Chave manual | GPIO 4 | Digital (pulldown) | — |

**Registradores Modbus lidos do SDM120 (endereço 1):**

| Registrador | Tipo | Descrição | Unidade |
|---|---|---|---|
| 0x0000 | FP32 | Tensão | V |
| 0x0006 | FP32 | Corrente | A |
| 0x000C | FP32 | Potência Ativa | W |
| 0x0012 | FP32 | Potência Aparente | VA |
| 0x0018 | FP32 | Potência Reativa | VAr |
| 0x001E | FP32 | Frequência | Hz |
| 0x0028 | FP32 | Fator de Potência | — |
| 0x0046 | FP32 | Energia Importada | kWh |

## 4. Tópicos MQTT

### 4.1 Estrutura de tópicos

O sufixo `{estacao}` é definido na configuração (padrão: `AeroClub Central`).

| Tópico | Direção | Finalidade |
|---|---|---|
| `Bal/Write/{estacao}` | Platforma → ESP32 | Comandos do balizador |
| `Bal/Read/{estacao}` | ESP32 → Plataforma | Status, consumo e confirmações |
| `SDM120/Write/{estacao}` | Plataforma → ESP32 | Comandos do medidor |
| `SDM120/Read/{estacao}` | ESP32 → Plataforma | Leituras dos registradores |
| `Heartbeat/{estacao}` | ESP32 → Plataforma | Heartbeat periódico |

### 4.2 Comandos recebidos (Bal/Write)

#### `BalOn`

Liga o relé da pista.

```json
{"comando": "BalOn"}
```
ou com parâmetros do agendamento:
```json
{
  "comando": "BalOn",
  "agendamento": {
    "id": 1,
    "data": "2026-07-17",
    "horario": "10:00",
    "hora_termino": "10:30",
    "duracao_minutos": 30
  }
}
```

**Resposta:** `publishStatus()` → `{"comando":"BalOn","estado":true,"timestamp":"..."}`

---

#### `BalOff`

Desliga o relé da pista.

```json
{"comando": "BalOff"}
```

**Resposta:** `publishConsumption()` + `publishStatus()` (BalOff:false)

---

#### `AgendarBalizamento`

Agenda uma ativação futura. O schedule é armazenado em NVS e executado automaticamente.

```json
{
  "comando": "AgendarBalizamento",
  "agendamento": {
    "id": 77,
    "data": "17/07/2026",
    "hora_inicio": "10:00:00",
    "hora_fim": "10:30:00",
    "duracao_segundos": 1800
  }
}
```

**Validações:**
- `id > 0`
- `hora_inicio` no futuro (`end_ts > now`)
- `hora_fim > hora_inicio`

**Resposta:** `publishScheduleStatus(id, "AgendamentoConfirmado", "agendado")`

---

#### `CancelarAgendamento`

Cancela um agendamento existente.

```json
{
  "comando": "CancelarAgendamento",
  "agendamento": {"id": 77}
}
```

**Resposta:** Nenhuma (remoção local).

---

#### `RequestHeartbeat`

Solicita heartbeat imediato.

```json
{"comando": "RequestHeartbeat"}
```

**Resposta:** `publishHeartbeat()` em `Heartbeat/{estacao}`.

---

#### `UpdateFirmware`

Atualização OTA via URL.

```json
{
  "comando": "UpdateFirmware",
  "url": "https://exemplo.com/firmware.bin"
}
```

**Resposta:** Nenhuma (OTA em andamento, dispositivo reinicia).

### 4.3 Comandos recebidos (SDM120/Write)

#### `ReadRegistersEnergy`

Solicita leitura dos registradores de energia do SDM120.

```json
{"comando": "ReadRegistersEnergy"}
```

**Resposta:** `publishEnergyRegisters()` em `SDM120/Read/{estacao}`.

### 4.4 Mensagens publicadas (Bal/Read)

#### `BalOn` / `BalOff`

Publicado por `publishStatus()` quando o estado do relé muda.

```json
{
  "comando": "BalOn",
  "estado": true,
  "timestamp": "17/07/2026 10:00:00"
}
```

#### `ConsumoBalizamento`

Publicado por `publishConsumption()` ao final de cada ativação.

```json
{
  "comando": "ConsumoBalizamento",
  "energia_inicial_kwh": 150.2,
  "energia_final_kwh": 150.8,
  "consumo_kwh": 0.6,
  "duracao_segundos": 1800,
  "duracao_minutos": 30.0,
  "timestamp": "17/07/2026 10:30:00"
}
```

#### `AgendamentoConfirmado` / `AgendamentoAndamento` / `AgendamentoFinalizado`

Publicado por `publishScheduleStatus()` nos três momentos do ciclo de vida do agendamento.

```json
{
  "comando": "AgendamentoConfirmado",
  "agendamento": {
    "id": 77,
    "status": "agendado",
    "data_hora": "17/07/2026 09:00:00"
  }
}
```

### 4.5 Mensagens publicadas (Heartbeat)

#### Heartbeat completo

Publicado a cada 300s e sob demanda via `RequestHeartbeat`.

```json
{
  "device": {
    "nome": "Balizamento Pista",
    "modelo": "ESP32",
    "serial": "ESP32-000001",
    "hardware": "RevA",
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.100",
    "hostname": "balizamento-pista",
    "esphome_version": "2025.12.0"
  },
  "firmware": {
    "versao": "2.0.5",
    "build_date": "Jul 17 2026 09:00:00",
    "md5": "d09ce4e70..."
  },
  "wifi": {
    "ssid": "MeuWiFi",
    "rssi": -45,
    "qualidade": 85,
    "ip": "192.168.1.100",
    "gateway": "192.168.1.1",
    "dns": "8.8.8.8",
    "mac": "AA:BB:CC:DD:EE:FF",
    "reconexoes": 0
  },
  "mqtt": {
    "broker": "192.168.1.10",
    "status": "Conectado",
    "mensagens_publicadas": 120,
    "mensagens_recebidas": 85,
    "ultima_reconexao": "2026-07-17T08:00:00"
  },
  "balizamento": {
    "status": "Inativo",
    "gpio": 2,
    "ultimo_comando": "BalOff",
    "ultimo_acionamento": "2026-07-17T08:30:00",
    "tempo_ligado_segundos": 3600,
    "contador_acionamentos": 15,
    "modo_manual": false
  },
  "sistema": {
    "uptime_segundos": 86400,
    "reinicios": 3,
    "heap_livre": 102400,
    "cpu_mhz": 240,
    "flash_livre": 1048576
  },
  "timestamp": "2026-07-17T09:00:00"
}
```

### 4.6 Mensagens publicadas (SDM120/Read)

#### Leitura de registradores

Resposta ao comando `ReadRegistersEnergy`.

```json
{
  "topic": "SDM120/Read/AeroClub Central",
  "payload": "ReadRegistersEnergy",
  "aeroclube_id": 1,
  "aeroclube_nome": "AeroClub Central",
  "confirmado": true,
  "timestamp": "17/07/2026 09:05:00",
  "equipamento": {
    "fabricante": "Eastron",
    "modelo": "SDM120",
    "numero_serie": "AA:BB:CC:DD:EE:FF",
    "firmware": "1.0.0"
  },
  "status": "OK",
  "registradores": {
    "0000": {"descricao": "Tensao", "valor": 220.5, "unidade": "V"},
    "0006": {"descricao": "Corrente", "valor": 2.3, "unidade": "A"},
    "000C": {"descricao": "Potencia Ativa", "valor": 480.0, "unidade": "W"},
    "0046": {"descricao": "Energia Importada", "valor": 150.2, "unidade": "kWh"}
  }
}
```

### 4.7 Sumário de fluxo — Agendamento

```
Plataforma                     ESP32                      SDM120
    |                            |                           |
    |--- Bal/Write ------------->|                           |
    |   AgendarBalizamento       |                           |
    |                            |                           |
    |<-- Bal/Read --------------|                           |
    |   AgendamentoConfirmado    |                           |
    |                            |                           |
    |       ... (tempo passa) ...|                           |
    |                            |                           |
    |                            |<--- Modbus -------------|
    |                            |     (leituras cíclicas)  |
    |                            |                           |
    |                            | (hora_inicio chegou)     |
    |                            | Liga relé (GPIO 2)       |
    |                            |                           |
    |<-- Bal/Read --------------|                           |
    |   AgendamentoAndamento     |                           |
    |                            |                           |
    |       ... (duração) ...    |                           |
    |                            |                           |
    |                            | (hora_fim chegou)        |
    |                            | Desliga relé (GPIO 2)    |
    |                            |                           |
    |<-- Bal/Read --------------|                           |
    |   ConsumoBalizamento       |                           |
    |<-- Bal/Read --------------|                           |
    |   AgendamentoFinalizado    |                           |
```

## 5. API HTTP (Web Server)

Servidor HTTP na porta 80, interface embarcada.

### 5.1 Página principal

**`GET /`** → HTML completo com CSS e JS embarcados (raw string literal).

### 5.2 Endpoints REST

#### `GET /api/status`

Retorna estado atual do dispositivo.

```json
{
  "relay_on": false,
  "timer_remaining_sec": 0,
  "timer_active": false,
  "wifi_ssid": "MeuWiFi",
  "wifi_rssi": -45,
  "wifi_ip": "192.168.1.100",
  "mqtt_connected": true,
  "manual_mode": false,
  "tensao": 220.5,
  "corrente": 2.3,
  "potencia": 480.0,
  "frequencia": 60.0,
  "energia_atual_kwh": 150.2,
  "last_consumo_kwh": 0.6,
  "last_duration_sec": 1800,
  "uptime_sec": 86400,
  "saved_ssid": "MeuWiFi",
  "saved_broker": "192.168.1.10",
  "timestamp": "17/07/2026 09:00:00"
}
```

#### `POST /api/control`

Liga ou desliga o relé.

**Request:**
```json
{"action": "on", "duration_min": 15}
```
```json
{"action": "off"}
```

**Response:** `{"success": true}`

#### `GET /api/history`

Histórico de ativações (máx. 10 registros).

```json
{
  "history": [
    {
      "date": "17/07/2026",
      "start_time": "08:00:00",
      "end_time": "08:30:00",
      "duration_sec": 1800,
      "energy_kwh": 0.6,
      "completed": true,
      "has_energy": true
    }
  ],
  "count": 1
}
```

#### `GET /api/schedules`

Agendamentos futuros.

```json
{
  "schedules": [
    {
      "id": 77,
      "start_timestamp": 1790000000,
      "end_timestamp": 1790001800,
      "duration_sec": 1800,
      "executed": false,
      "start": "17/07/2026 10:00:00",
      "end": "17/07/2026 10:30:00"
    }
  ],
  "count": 1
}
```

#### `GET /api/config`

Configuração salva em NVS.

```json
{
  "wifi_ssid": "MeuWiFi",
  "mqtt_broker": "192.168.1.10",
  "mqtt_port": 1883,
  "mqtt_username": "",
  "mqtt_topic_suffix": "AeroClub Central",
  "timezone": "America/Sao_Paulo"
}
```

#### `POST /api/config`

Salva configuração (requer reboot).

**Request:**
```json
{
  "wifi_ssid": "MeuWiFi",
  "wifi_password": "senha",
  "mqtt_broker": "192.168.1.10",
  "mqtt_port": 1883,
  "mqtt_username": "",
  "mqtt_password": "",
  "mqtt_topic_suffix": "AeroClub Central",
  "timezone": "America/Sao_Paulo"
}
```

**Response:** `{"success": true, "needs_reboot": true}`

#### `GET /api/scan`

Escaneia redes WiFi disponíveis.

```json
{
  "networks": [
    {"ssid": "MeuWiFi", "rssi": -45, "channel": 6, "auth": 4}
  ]
}
```

#### `POST /api/ota`

Atualização OTA.

**Request:** `{"url": "https://exemplo.com/firmware.bin"}`

**Response:** `{"success": true}`

#### `POST /api/restart`

Reinicia o ESP32.

**Response:** `{"success": true}`

## 6. Armazenamento (NVS)

Namespace: `balizamento`

| Chave | Tipo | Conteúdo |
|---|---|---|
| `config` | blob (`SavedConfig`) | Configuração WiFi, MQTT, timezone |
| `schedule_count` | i32 | Número de agendamentos salvos |
| `schedule_N` | blob (`ScheduledEvent`) | Agendamento N |
| `history_count` | i32 | Número de registros históricos |
| `rec_N` | blob (`HistoryEntry`) | Registro histórico N |

## 7. Estruturas de Dados

### `SavedConfig` (config)

| Campo | Tipo | Tam. | Descrição |
|---|---|---|---|
| `wifi_ssid` | char[] | 33 | SSID da rede WiFi |
| `wifi_password` | char[] | 65 | Senha WiFi |
| `mqtt_broker` | char[] | 129 | Endereço do broker |
| `mqtt_port` | uint16_t | 2 | Porta MQTT |
| `mqtt_username` | char[] | 65 | Usuário MQTT |
| `mqtt_password` | char[] | 65 | Senha MQTT |
| `mqtt_topic_suffix` | char[] | 65 | Sufixo dos tópicos |
| `timezone` | char[] | 33 | Fuso horário (IANA) |

### `ScheduledEvent`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | uint32_t | ID único do agendamento |
| `start_timestamp` | uint32_t | Unix timestamp de início |
| `end_timestamp` | uint32_t | Unix timestamp de fim |
| `duration_sec` | uint32_t | Duração em segundos |
| `executed` | bool | Se já foi executado |

### `HistoryEntry`

| Campo | Tipo | Descrição |
|---|---|---|
| `timestamp` | uint32_t | Unix timestamp do fim |
| `duration_sec` | uint32_t | Duração em segundos |
| `energy_kwh` | float | Energia consumida |
| `completed` | bool | Se finalizou normalmente |
| `has_energy` | bool | Se havia dado de energia |

## 8. Timezone

O ESPHome não chama `setenv("TZ")`/`tzset()` em plataformas embarcadas. O firmware chama explicitamente com formato POSIX (ex.: `BRT3`) para que `mktime()` interprete `struct tm` como hora local.

A string POSIX é derivada do campo `timezone` da configuração:

| Config timezone | POSIX |
|---|---|
| `America/Sao_Paulo` (padrão) | `BRT3` |
| `America/Manaus` | `BRT4` |
| `America/Noronha` | `BRT2` |

## 9. Dependências

| Biblioteca | Versão | Uso |
|---|---|---|
| ESPHome | 2025.12 | Framework base |
| ArduinoJson | 7.4.3 | Serialização JSON |
| ESP-IDF | 5.5.4 | SDK do ESP32 |
| mqtt_client (ESPHome) | — | Cliente MQTT |
| modbus_controller (ESPHome) | — | Leitura SDM120 |
