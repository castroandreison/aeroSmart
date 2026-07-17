#pragma once

#include "esphome.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/mqtt/mqtt_client.h"

#include <ArduinoJson.h>

#include <esp_wifi.h>
#include <esp_netif.h>
#include <esp_mac.h>
#include <esp_http_server.h>
#include <esp_http_client.h>
#include <esp_ota_ops.h>
#include <esp_partition.h>
#include <nvs_flash.h>
#include <mbedtls/md.h>
#include <cstring>
#include <string>
#include <vector>
#include <ctime>
#include <cstdlib>

static const char *TAG = "balizamento";

#define BAL_READ_BASE    "Bal/Read/"
#define BAL_WRITE_BASE   "Bal/Write/"
#define SDM_READ_BASE    "SDM120/Read/"
#define SDM_WRITE_BASE   "SDM120/Write/"
#define HEARTBEAT_BASE   "Heartbeat/"
#define RELAY_PIN        GPIO_NUM_2
#define MANUAL_PIN       GPIO_NUM_4
#define MAX_HISTORY      10
#define MAX_SCHEDULES    20
#define NVS_NAMESPACE    "balizamento"

#ifndef TUYA_PRODUCT_ID
#define TUYA_PRODUCT_ID  ""
#endif
#ifndef TUYA_DEVICE_ID
#define TUYA_DEVICE_ID   ""
#endif
#ifndef TUYA_CLIENT_ID
#define TUYA_CLIENT_ID   ""
#endif
#ifndef TUYA_SECRET
#define TUYA_SECRET      ""
#endif
#ifndef TUYA_REGION
#define TUYA_REGION      "m2.tuyaeu.com"
#endif

static std::string g_tuya_pid = TUYA_PRODUCT_ID;
static std::string g_tuya_did = TUYA_DEVICE_ID;
static std::string g_tuya_cid = TUYA_CLIENT_ID;
static std::string g_tuya_sec = TUYA_SECRET;
static std::string g_tuya_reg = TUYA_REGION;

// Heartbeat / Firmware metadata
#ifndef FIRMWARE_VERSION
#define FIRMWARE_VERSION "2.0.5"
#endif
#ifndef FIRMWARE_BIN
#define FIRMWARE_BIN "balizador_v2.0.5.bin"
#endif
#ifndef FIRMWARE_OTA_CHANNEL
#define FIRMWARE_OTA_CHANNEL "stable"
#endif

#ifndef FIRMWARE_VERSION_URL
#define FIRMWARE_VERSION_URL "https://gitlab.com/castroandreison/aerocontrol/-/raw/main/version.json"
#endif
#ifndef FIRMWARE_URL
#define FIRMWARE_URL "https://gitlab.com/castroandreison/aerocontrol/-/raw/main/latest.ota.bin"
#endif
#ifndef FIRMWARE_MD5_URL
#define FIRMWARE_MD5_URL "https://gitlab.com/castroandreison/aerocontrol/-/raw/main/latest.md5"
#endif
#ifndef DEVICE_SERIAL
#define DEVICE_SERIAL "ESP32-000001"
#endif
#ifndef DEVICE_HARDWARE
#define DEVICE_HARDWARE "RevA"
#endif

class BalizamentoController;
extern BalizamentoController *g_controller;
void sdm120_on_message(const std::string &payload);

struct ActivationRecord {
  char timestamp[20];
  uint32_t duration_sec;
  float energy_kwh;
  bool completed;
  bool has_energy;
};

static const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Balizamento - Pista</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0b0e14;color:#e0e4ec;padding:16px}
.container{max-width:600px;margin:0 auto}
.card{background:#151b26;border-radius:12px;padding:16px;margin-bottom:16px}
h1{font-size:20px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:1px;color:#8892a4;margin-bottom:12px}
.status{display:flex;gap:12px;flex-wrap:wrap}
.badge{padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600}
.badge-on{background:#1a6b3c;color:#4cdf8b}
.badge-off{background:#5c1f1f;color:#ff6b6b}
.badge-warn{background:#6b5c1f;color:#ffd93d}
.badge-err{background:#3a1f3a;color:#ff6b9d}
.timer{font-size:42px;font-weight:700;text-align:center;padding:16px 0;font-family:monospace;letter-spacing:2px}
.controls{display:flex;gap:8px;flex-wrap:wrap}
.controls input{flex:1;min-width:100px;padding:10px 12px;border-radius:8px;border:1px solid #2a3346;background:#0b0e14;color:#e0e4ec;font-size:15px}
.controls button{flex:1;padding:10px 16px;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}
.btn-on{background:#1a6b3c;color:#fff}.btn-off{background:#6b1f1f;color:#fff}
.btn-danger{background:#8b3a3a;color:#fff}.btn-primary{background:#2a5c8a;color:#fff}
.readings{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.reading{padding:12px;background:#0b0e14;border-radius:8px;text-align:center}
.reading .val{font-size:22px;font-weight:700}.reading .lbl{font-size:11px;color:#8892a4}
.consumo-box{padding:12px;background:#0f1a2e;border-radius:8px;margin-top:8px;text-align:center}
.consumo-box .val{font-size:28px;color:#4c9aff}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 4px;text-align:left;border-bottom:1px solid #1f2838}
th{color:#8892a4;font-size:11px;text-transform:uppercase}
.ota-section{display:flex;gap:8px;flex-wrap:wrap}
.ota-section input{flex:1;min-width:150px;padding:10px 12px;border-radius:8px;border:1px solid #2a3346;background:#0b0e14;color:#e0e4ec;font-size:14px}
.timestamp{font-size:11px;color:#5a6a7e;margin-top:8px}
#wifiDetail{font-size:12px;color:#8892a4;margin-top:4px}
@media(max-width:400px){.readings{grid-template-columns:1fr}.controls{flex-direction:column}}
</style>
</head>
<body>
<div class="container">
<div class="card">
<h1>Balizamento Pista</h1>
<div class="status">
<span class="badge badge-off" id="relayBadge">Desligado</span>
<span class="badge badge-off" id="wifiBadge">WiFi</span>
<span class="badge badge-off" id="mqttBadge">MQTT</span>
<span class="badge badge-off" id="modeBadge">Auto</span>
</div>
<div class="timestamp" id="ipDisplay"></div>
<div id="wifiDetail"></div>
</div>
<div class="card">
<h2>Controle</h2>
<div class="timer" id="timerDisplay">--:--:--</div>
<div class="controls">
<input type="number" id="durationInput" placeholder="Duracao (min)" min="0" step="1">
<button class="btn-on" onclick="sendCmd('on')">Ligar</button>
<button class="btn-off" onclick="sendCmd('off')">Desligar</button>
</div>
</div>
<div class="card">
<h2>Medidor SDM120</h2>
<div class="readings">
<div class="reading"><div class="val" id="rTensao">--</div><div class="lbl">Tensao</div></div>
<div class="reading"><div class="val" id="rCorrente">--</div><div class="lbl">Corrente</div></div>
<div class="reading"><div class="val" id="rPotencia">--</div><div class="lbl">Potencia</div></div>
<div class="reading"><div class="val" id="rFreq">--</div><div class="lbl">Frequencia</div></div>
</div>
<div class="consumo-box">
<div style="font-size:12px;color:#8892a4">Ultimo Consumo</div>
<div class="val" id="lastConsumo">-- kWh</div>
<div style="font-size:12px;color:#5a6a7e" id="lastConsumoDur"></div>
</div>
</div>
<div class="card">
<h2>Historico</h2>
<table>
<thead><tr><th>Data</th><th>Horario Inicio</th><th>Horario Fim</th><th>Duracao</th><th>Consumo</th><th>Status</th></tr></thead>
<tbody id="historyBody"><tr><td colspan="6">Carregando...</td></tr></tbody>
</table>
</div>
<div class="card">
<h2>Agendamentos Futuros</h2>
<table>
<thead><tr><th>Inicio</th><th>Fim</th><th>Duracao</th><th>Status</th></tr></thead>
<tbody id="schedulesBody"><tr><td colspan="4">Carregando...</td></tr></tbody>
</table>
</div>
<div class="card">
<h2>MQTT Log</h2>
<div style="max-height:300px;overflow-y:auto;font-size:11px">
<table>
<thead><tr><th>Topico</th><th>Payload</th><th>Quando</th></tr></thead>
<tbody id="mqttLogBody"><tr><td colspan="3" style="text-align:center;color:#5a6a7e">Aguardando...</td></tr></tbody>
</table>
</div>
</div>
<div class="card">
<h2>Configuracoes</h2>
<div style="display:flex;gap:4px;margin-bottom:12px">
<button class="btn-primary" style="flex:1;font-size:13px;padding:6px" onclick="showTab('rede')">Rede</button>
<button class="btn-primary" style="flex:1;font-size:13px;padding:6px" onclick="showTab('mqtt')">MQTT</button>
<button class="btn-primary" style="flex:1;font-size:13px;padding:6px" onclick="showTab('geral')">Geral</button>
</div>
<div id="tabRede">
<div style="display:grid;gap:8px">
<input type="text" id="cfgSsid" placeholder="WiFi SSID">
<input type="password" id="cfgPass" placeholder="WiFi Senha">
<button class="btn-primary" style="font-size:13px;padding:6px" onclick="scanNetworks()">Buscar Redes</button>
<select id="netList" style="display:none;padding:6px;border-radius:8px;border:1px solid #2a3346;background:#0b0e14;color:#e0e4ec" onchange="document.getElementById('cfgSsid').value=this.value"></select>
<button class="btn-on" onclick="saveConfig()">Salvar e Reiniciar</button>
</div>
</div>
<div id="tabMqtt" style="display:none">
<div style="display:grid;gap:8px">
<input type="text" id="cfgBroker" placeholder="MQTT Broker (ex: broker.emqx.io)">
<input type="number" id="cfgPort" placeholder="MQTT Port (1883)" min="1" max="65535">
<input type="text" id="cfgSuffix" placeholder="Sufixo topico (ex: AeroClub Central)">
<select id="cfgTz">
<option value="America/Sao_Paulo">America/Sao_Paulo (BRT)</option>
<option value="America/Manaus">America/Manaus (AMT)</option>
<option value="America/Belem">America/Belem (BRT)</option>
<option value="America/Fortaleza">America/Fortaleza (BRT)</option>
<option value="America/Noronha">America/Noronha (FNT)</option>
<option value="America/Boa_Vista">America/Boa_Vista (AMT)</option>
<option value="America/Cuiaba">America/Cuiaba (AMT)</option>
<option value="America/Campo_Grande">America/Campo_Grande (AMT)</option>
<option value="America/Santarem">America/Santarem (BRT)</option>
<option value="America/Porto_Velho">America/Porto_Velho (AMT)</option>
<option value="America/Rio_Branco">America/Rio_Branco (ACT)</option>
<option value="America/Maceio">America/Maceio (BRT)</option>
<option value="-03">UTC-3 (Brasilia)</option>
<option value="-04">UTC-4 (Amazonas)</option>
<option value="-05">UTC-5 (Acre)</option>
<option value="-02">UTC-2 (Fernando Noronha)</option>
</select>
<button class="btn-on" onclick="saveConfig()">Salvar e Reiniciar</button>
</div>
</div>
<div id="tabGeral" style="display:none">
<div class="ota-section">
<input type="url" id="otaUrl" placeholder="URL do firmware (.bin)">
<button class="btn-danger" onclick="doOTA()">Atualizar FW</button>
</div>
<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
<button class="btn-primary" onclick="restartESP()">Reiniciar</button>
</div>
</div>
</div>
</div>
<script>
async function fetchJSON(url,opts){
  try{
    const r=await fetch(url,opts);return await r.json();
  }catch(e){return null}
}
function fmtTime(s){
  if(s==null||s<0)return'--:--:--';
  const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;
  return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');
}
async function fetchStatus(){
  const d=await fetchJSON('/api/status');
  if(!d)return;
  document.getElementById('relayBadge').textContent=d.relay_on?'Ligado':'Desligado';
  document.getElementById('relayBadge').className='badge '+(d.relay_on?'badge-on':'badge-off');
  document.getElementById('timerDisplay').textContent=fmtTime(d.timer_remaining);
  if(d.wifi){
    const rssi=d.rssi||-100;
    let c='badge-on',co='#4cdf8b';
    if(rssi<-67){c='badge-warn';co='#ffd93d'}
    if(rssi<-80){c='badge-off';co='#ff6b6b'}
    document.getElementById('wifiBadge').textContent=rssi+' dBm';
    document.getElementById('wifiBadge').className='badge '+c;
    document.getElementById('wifiDetail').innerHTML='<b>'+d.ssid+'</b> | <span style="color:'+co+'">'+d.wifi_quality+'</span>';
  }else{
    document.getElementById('wifiBadge').textContent='WiFi:(';
    document.getElementById('wifiBadge').className='badge badge-err';
  }
  document.getElementById('mqttBadge').textContent=d.mqtt?'MQTT OK':'MQTT:(';
  document.getElementById('mqttBadge').className='badge '+(d.mqtt?'badge-on':'badge-err');
  const manual=d.modo_manual;
  document.getElementById('modeBadge').textContent=manual?'Manual':'Auto';
  document.getElementById('modeBadge').className='badge '+(manual?'badge-warn':'badge-on');
  document.getElementById('ipDisplay').textContent='IP: '+d.ip;
  if(d.energy){
    document.getElementById('rTensao').textContent=d.energy.tensao||'--';
    document.getElementById('rCorrente').textContent=d.energy.corrente||'--';
    document.getElementById('rPotencia').textContent=d.energy.potencia||'--';
    document.getElementById('rFreq').textContent=d.energy.frequencia||'--';
  }
  if(d.last_consumo!=null){
    document.getElementById('lastConsumo').textContent=d.last_consumo.toFixed(3)+' kWh';
    document.getElementById('lastConsumoDur').textContent='Duracao: '+fmtTime(d.last_duration||0);
  }
}
async function fetchHistory(){
  const d=await fetchJSON('/api/history');
  if(!d)return;
  const tbody=document.getElementById('historyBody');
  tbody.innerHTML='';
  if(!d.history||d.history.length===0){
    tbody.innerHTML='<tr><td colspan="6" style="text-align:center;color:#5a6a7e">Nenhum registro</td></tr>';
    return;
  }
  for(const h of d.history){
    const tr=document.createElement('tr');
    const e=h.has_energy?h.energy_kwh.toFixed(3):'--';
    tr.innerHTML='<td>'+h.date+'</td><td>'+h.start_time+'</td><td>'+h.end_time+'</td><td>'+fmtTime(h.duration_sec)+'</td><td>'+e+' kWh</td><td>'+(h.completed?'OK':'Interrompido')+'</td>';
    tbody.appendChild(tr);
  }
}
async function fetchSchedules(){
  const d=await fetchJSON('/api/schedules');
  if(!d)return;
  const tbody=document.getElementById('schedulesBody');
  tbody.innerHTML='';
  if(!d.schedules||d.schedules.length===0){
    tbody.innerHTML='<tr><td colspan="4" style="text-align:center;color:#5a6a7e">Nenhum agendamento futuro</td></tr>';
    return;
  }
  for(const s of d.schedules){
    const tr=document.createElement('tr');
    const status=s.executed?'Em Andamento':'Pendente';
    const sc=s.executed?'badge-on':'badge-warn';
    tr.innerHTML='<td>'+s.start+'</td><td>'+s.end+'</td><td>'+fmtTime(s.duration_sec)+'</td><td><span class="badge '+sc+'" style="font-size:11px;padding:2px 8px">'+status+'</span></td>';
    tbody.appendChild(tr);
  }
}
async function sendCmd(action){
  const dur=document.getElementById('durationInput').value;
  const body={action:action};
  if(action==='on'&&dur>0)body.duration_min=parseFloat(dur);
  await fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
}
async function doOTA(){
  const url=document.getElementById('otaUrl').value.trim();
  if(!url||!url.startsWith('http'))return alert('URL invalida');
  if(!confirm('ATENCAO: O dispositivo sera reiniciado. Continuar?'))return;
  await fetch('/api/ota',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url})});
  alert('OTA iniciado! O dispositivo sera reiniciado.');
}
async function restartESP(){
  if(!confirm('Reiniciar dispositivo?'))return;
  await fetch('/api/restart',{method:'POST'});
}
async function scanNetworks(){
  const btn=document.querySelector('[onclick="scanNetworks()"]');
  btn.textContent='Buscando...';
  btn.disabled=true;
  const d=await fetchJSON('/api/scan');
  btn.textContent='Buscar Redes';
  btn.disabled=false;
  const sel=document.getElementById('netList');
  sel.innerHTML='<option value="">-- Selecione uma rede --</option>';
  if(d&&d.networks){
    const seen={};
    for(const n of d.networks){
      if(!n.ssid||seen[n.ssid])continue;
      seen[n.ssid]=true;
      const o=document.createElement('option');
      o.value=n.ssid;
      o.textContent=n.ssid+(n.auth=='protegida'?' 🔒':' 🔓')+' ('+n.rssi+' dBm)';
      sel.appendChild(o);
    }
  }
  sel.style.display='block';
}
function showTab(tab){
  document.getElementById('tabRede').style.display=tab==='rede'?'block':'none';
  document.getElementById('tabMqtt').style.display=tab==='mqtt'?'block':'none';
  document.getElementById('tabGeral').style.display=tab==='geral'?'block':'none';
}
async function loadConfig(){
  const d=await fetchJSON('/api/config');
  if(!d)return;
  document.getElementById('cfgSsid').value=d.wifi_ssid||'';
  document.getElementById('cfgBroker').value=d.mqtt_broker||'';
  document.getElementById('cfgPort').value=d.mqtt_port||1883;
  document.getElementById('cfgSuffix').value=d.mqtt_topic_suffix||'AeroClub Central';
  if(d.timezone){
    const sel=document.getElementById('cfgTz');
    for(let o of sel.options)if(o.value===d.timezone){o.selected=true;break}
  }
}
async function saveConfig(){
  const body={
    wifi_ssid:document.getElementById('cfgSsid').value.trim(),
    wifi_password:document.getElementById('cfgPass').value,
    mqtt_broker:document.getElementById('cfgBroker').value.trim(),
    mqtt_port:parseInt(document.getElementById('cfgPort').value)||1883,
    mqtt_topic_suffix:document.getElementById('cfgSuffix').value.trim(),
    timezone:document.getElementById('cfgTz').value,
    mqtt_username:'',
    mqtt_password:''
  };
  const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=r?await r.json():null;
  if(d&&d.success){
    alert('Configuracoes salvas! O dispositivo sera reiniciado.');
    restartESP();
  }else{
    alert('Erro ao salvar configuracoes.');
  }
}
fetchStatus();fetchHistory();fetchSchedules();loadConfig();
setInterval(fetchStatus,1000);setInterval(fetchHistory,10000);setInterval(fetchSchedules,10000);
</script>
</body>
</html>
)rawliteral";

struct HistoryEntry {
  uint32_t timestamp;
  uint32_t duration_sec;
  float energy_kwh;
  bool completed;
  bool has_energy;
};

struct ScheduledEvent {
  uint32_t id;
  uint32_t start_timestamp;
  uint32_t end_timestamp;
  uint32_t duration_sec;
  bool executed;
};

struct SavedConfig {
  char wifi_ssid[33];
  char wifi_password[65];
  char mqtt_broker[129];
  uint16_t mqtt_port;
  char mqtt_username[65];
  char mqtt_password[65];
  char mqtt_topic_suffix[65];
  char timezone[33];
};

class BalizamentoController : public esphome::Component {
 public:
  bool relay_on_ = false;
  bool timer_active_ = false;
  unsigned long timer_start_ms_ = 0;
  unsigned long timer_duration_ms_ = 0;
  float energy_start_kwh_ = 0;
  float energy_end_kwh_ = 0;
  float current_energy_ = 0;
  float current_tensao_ = 0;
  float current_corrente_ = 0;
  float current_potencia_ = 0;
  float current_frequencia_ = 0;
  float last_consumo_ = 0;
  unsigned long last_duration_sec_ = 0;
  bool has_energy_data_ = false;
  unsigned long last_ms_ = 0;
  bool isManualMode() { return gpio_get_level(MANUAL_PIN) == 1; }

 public:
  BalizamentoController() {}

  void setup() override;
  void loop() override;
  float get_setup_priority() const override {
    return esphome::setup_priority::AFTER_WIFI + 10;
  }

  void handleBalCommand(const std::string &payload, float energia);
  void setCurrentEnergy(float v) { current_energy_ = v; has_energy_data_ = !std::isnan(v); }
  void setTensao(float v) { current_tensao_ = v; }
  void setCorrente(float v) { current_corrente_ = v; }
  void setPotencia(float v) { current_potencia_ = v; }
  void setFrequencia(float v) { current_frequencia_ = v; }

  // Heartbeat
  void publishHeartbeat();
  void onWiFiConnected();
  void onMqttConnected();
  void onMqttDisconnected();

  SavedConfig getConfig() { return saved_config_; }
  void loadSavedConfig();
  void saveConfig(const SavedConfig &cfg);
  void reconnectWiFi();
  void startAP();

  static void setTuyaConfig(const char *pid, const char *did, const char *cid, const char *sec, const char *reg) {
    if (pid) g_tuya_pid = pid;
    if (did) g_tuya_did = did;
    if (cid) g_tuya_cid = cid;
    if (sec) g_tuya_sec = sec;
    if (reg) g_tuya_reg = reg;
  }

 private:
  httpd_handle_t server_ = NULL;
  bool ap_started_ = false;
  bool tuya_ok_ = false;
  unsigned long last_tuya_reconnect_ = 0;
  nvs_handle_t nvs_handle_;
  std::vector<HistoryEntry> history_;
  std::vector<ScheduledEvent> schedule_queue_;
  unsigned long last_schedule_check_ms_ = 0;
  SavedConfig saved_config_;

  std::string bal_read_topic_;
  std::string bal_write_topic_;
  std::string sdm_read_topic_;
  std::string sdm_write_topic_;
  std::string heartbeat_topic_;

  void buildTopics() {
    const char *suf = saved_config_.mqtt_topic_suffix;
    if (strlen(suf) == 0) suf = "AeroClub Central";
    bal_read_topic_  = std::string(BAL_READ_BASE)  + suf;
    bal_write_topic_ = std::string(BAL_WRITE_BASE) + suf;
    sdm_read_topic_  = std::string(SDM_READ_BASE)  + suf;
    sdm_write_topic_ = std::string(SDM_WRITE_BASE) + suf;
    heartbeat_topic_ = std::string(HEARTBEAT_BASE) + suf;
  }

  void initWebServer();
  void checkTimer();
  void finishActivation(bool completed);
  void loadHistory();
  void saveHistory();
  void addHistory(uint32_t dur, float energy, bool completed, bool has_energy);

  void loadSchedules();
  void saveSchedules();
  void checkSchedules();
  void cleanupSchedules();
  static time_t parseScheduleDateTime(const char *date, const char *time_str);
  void publishScheduleStatus(uint32_t id, const char *comando, const char *status);

  // Heartbeat tracking
  int mqtt_published_count_ = 0;
  int mqtt_received_count_ = 0;
  bool has_pending_consumption_ = false;
  float pending_consumption_kwh_ = 0;
  unsigned long pending_duration_sec_ = 0;
  int wifi_reconnect_count_ = 0;
  int restart_count_ = 0;
  int activation_count_ = 0;
  unsigned long total_on_time_ms_ = 0;
  unsigned long last_mqtt_connect_ms_ = 0;
  time_t last_mqtt_connect_time_ = 0;
  std::string last_command_;
  std::string last_activation_timestamp_;
  std::string app_sha256_;
  bool mqtt_was_connected_ = false;
  bool wifi_was_connected_ = false;
  bool heartbeat_initialized_ = false;

 public:
  void publishStatus();
  void publishConsumption(float diff_kwh, unsigned long dur_sec);
  void publishEnergyRegisters();
  void incrementMqttReceivedCount() { mqtt_received_count_++; }
  const std::string &getSdmWriteTopic() const { return sdm_write_topic_; }

  void initTuya();
  void checkTuya();
  static std::string tuyaHmacSha256(const std::string &key, const std::string &msg);
  void performOTA(const std::string &url);

  static void getWiFiInfo(int &rssi, std::string &ssid, std::string &ip, std::string &mac, bool &connected);
  static std::string fmtTimestamp(time_t t);
  static std::string fmtDate(time_t t);

  static esp_err_t handleRoot(httpd_req_t *req);
  static esp_err_t handleApiStatus(httpd_req_t *req);
  static esp_err_t handleApiControl(httpd_req_t *req);
  static esp_err_t handleApiHistory(httpd_req_t *req);
  static esp_err_t handleApiOTA(httpd_req_t *req);
  static esp_err_t handleApiRestart(httpd_req_t *req);
  static esp_err_t handleApiConfig(httpd_req_t *req);
  static esp_err_t handleApiScan(httpd_req_t *req);
  static esp_err_t handleApiSchedules(httpd_req_t *req);
};

BalizamentoController *g_controller = nullptr;

// ==================== WIFI INFO ====================
void BalizamentoController::getWiFiInfo(int &rssi, std::string &ssid, std::string &ip, std::string &mac, bool &connected) {
  rssi = 0; ssid.clear(); ip.clear(); mac.clear(); connected = false;
  wifi_ap_record_t ap = {};
  if (esp_wifi_sta_get_ap_info(&ap) == ESP_OK) {
    rssi = ap.rssi;
    ssid = std::string((char *)ap.ssid);
    connected = true;
  }
  esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
  if (netif) {
    esp_netif_ip_info_t info;
    if (esp_netif_get_ip_info(netif, &info) == ESP_OK) {
      char buf[16];
      esp_ip4addr_ntoa(&info.ip, buf, sizeof(buf));
      ip = buf;
    }
  }
  uint8_t m[6];
  if (esp_read_mac(m, ESP_MAC_WIFI_STA) == ESP_OK) {
    char buf[18];
    snprintf(buf, sizeof(buf), "%02X:%02X:%02X:%02X:%02X:%02X", m[0], m[1], m[2], m[3], m[4], m[5]);
    mac = buf;
  }
}

// ==================== TIMESTAMP ====================
std::string BalizamentoController::fmtTimestamp(time_t t) {
  if (t < 100000) {
    unsigned long ms = (unsigned long)(esp_timer_get_time() / 1000);
    unsigned long sec = ms / 1000, mi = sec / 60, hr = mi / 60;
    char buf[25];
    snprintf(buf, sizeof(buf), "UP %02lu:%02lu:%02lu", hr % 24, mi % 60, sec % 60);
    return std::string(buf);
  }
  struct tm *ti = localtime(&t);
  char buf[25];
  snprintf(buf, sizeof(buf), "%02d/%02d/%04d %02d:%02d:%02d",
           ti->tm_mday, ti->tm_mon + 1, ti->tm_year + 1900, ti->tm_hour, ti->tm_min, ti->tm_sec);
  return std::string(buf);
}

std::string BalizamentoController::fmtDate(time_t t) {
  if (t < 100000) return std::string("--/--/----");
  struct tm *ti = localtime(&t);
  char buf[12];
  snprintf(buf, sizeof(buf), "%02d/%02d/%04d", ti->tm_mday, ti->tm_mon + 1, ti->tm_year + 1900);
  return std::string(buf);
}

static std::string fmtTime(time_t t) {
  if (t < 100000) return std::string("--:--:--");
  struct tm *ti = localtime(&t);
  char buf[10];
  snprintf(buf, sizeof(buf), "%02d:%02d:%02d", ti->tm_hour, ti->tm_min, ti->tm_sec);
  return std::string(buf);
}

// ==================== SETUP ====================
void BalizamentoController::setup() {
  ESP_LOGI(TAG, "Inicializando...");
  g_controller = this;

  gpio_set_direction(RELAY_PIN, GPIO_MODE_OUTPUT);
  gpio_set_level(RELAY_PIN, 0);
  relay_on_ = false;
  gpio_set_direction(MANUAL_PIN, GPIO_MODE_INPUT);
  gpio_set_pull_mode(MANUAL_PIN, GPIO_PULLDOWN_ONLY);

  loadHistory();
  loadSchedules();
  loadSavedConfig();
  buildTopics();
  // Aplicar timezone (formato POSIX, necessario para mktime)
  {
    int off_h = 3; // default BRT (UTC-3)
    const char *tz = saved_config_.timezone;
    if (strlen(tz) > 0) {
      int h = 0;
      if (sscanf(tz, "%d", &h) == 1 && h >= -12 && h <= 12) {
        off_h = -h;
      } else if (strstr(tz, "Noronha") || strcmp(tz, "-02") == 0) {
        off_h = 2;
      } else if (strstr(tz, "Manaus") || strstr(tz, "Boa_Vista") || strstr(tz, "Cuiaba") ||
                 strstr(tz, "Campo_Grande") || strstr(tz, "Porto_Velho") || strcmp(tz, "-04") == 0) {
        off_h = 4;
      } else if (strstr(tz, "Rio_Branco") || strcmp(tz, "-05") == 0) {
        off_h = 5;
      }
    }
    char tz_buf[32];
    snprintf(tz_buf, sizeof(tz_buf), "BRT%d", off_h);
    setenv("TZ", tz_buf, 1);
    tzset();
  }
  ap_started_ = true; // AP gerenciado pelo YAML
  if (strlen(saved_config_.wifi_ssid) > 0) {
    reconnectWiFi();
  }
  initWebServer();
  initTuya();

  {
    int rssi; std::string ssid, ip, mac; bool wk;
    getWiFiInfo(rssi, ssid, ip, mac, wk);
    if (wk) {
      ESP_LOGI(TAG, "WiFi conectado - SSID: %s, IP: %s, RSSI: %d", ssid.c_str(), ip.c_str(), rssi);
    } else {
      ESP_LOGI(TAG, "Modo AP - Rede: AeroControl, IP: 192.168.4.1");
    }
  }

  // Increment restart counter in NVS
  {
    nvs_handle_t h;
    if (nvs_open("heartbeat", NVS_READWRITE, &h) == ESP_OK) {
      int32_t v = 0;
      nvs_get_i32(h, "restarts", &v);
      v++;
      restart_count_ = (int)v;
      nvs_set_i32(h, "restarts", v);
      nvs_commit(h);
      nvs_close(h);
    }
  }

  // Publish initial heartbeat (will queue until MQTT connects)
  ESP_LOGI(TAG, "Setup concluido");
}

void BalizamentoController::loop() {
  checkTimer();
  checkTuya();

  // Check schedules every 2 seconds
  unsigned long now_ms = (unsigned long)(esp_timer_get_time() / 1000);
  if (now_ms - last_schedule_check_ms_ >= 2000) {
    last_schedule_check_ms_ = now_ms;
    checkSchedules();
  }

  // Detect MQTT connection state changes
  bool mqtt_now = esphome::mqtt::global_mqtt_client &&
                   esphome::mqtt::global_mqtt_client->is_connected();
  if (mqtt_now && !mqtt_was_connected_) {
    onMqttConnected();
  } else if (!mqtt_now && mqtt_was_connected_) {
    onMqttDisconnected();
  }

  // Detect WiFi connection state changes
  wifi_ap_record_t ap = {};
  bool wifi_now = (esp_wifi_sta_get_ap_info(&ap) == ESP_OK);
  if (wifi_now && !wifi_was_connected_) {
    wifi_was_connected_ = true;
  } else if (!wifi_now && wifi_was_connected_) {
    wifi_was_connected_ = false;
  }

  // Track total on time
  if (relay_on_) {
    total_on_time_ms_ += 50;
  }
}

// ==================== WEB SERVER ====================
void BalizamentoController::initWebServer() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.max_uri_handlers = 20;
  cfg.lru_purge_enable = true;

  if (httpd_start(&server_, &cfg) == ESP_OK) {
    httpd_uri_t uris[] = {
      {"/",              HTTP_GET,  handleRoot,       NULL},
      {"/api/status",    HTTP_GET,  handleApiStatus,  NULL},
      {"/api/control",   HTTP_POST, handleApiControl, NULL},
      {"/api/history",   HTTP_GET,  handleApiHistory, NULL},
      {"/api/ota",       HTTP_POST, handleApiOTA,       NULL},
      {"/api/restart",   HTTP_POST, handleApiRestart,   NULL},
      {"/api/config",    HTTP_GET,  handleApiConfig,    NULL},
      {"/api/config",    HTTP_POST, handleApiConfig,    NULL},
      {"/api/scan",      HTTP_GET,  handleApiScan,       NULL},
      {"/api/schedules", HTTP_GET,  handleApiSchedules,  NULL},
    };
    for (auto &u : uris) httpd_register_uri_handler(server_, &u);
    ESP_LOGI(TAG, "Web server iniciado na porta 80");
  } else {
    ESP_LOGE(TAG, "Falha ao iniciar web server");
  }
}

esp_err_t BalizamentoController::handleRoot(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  httpd_resp_set_hdr(req, "Cache-Control", "no-cache");
  httpd_resp_send(req, INDEX_HTML, strlen(INDEX_HTML));
  return ESP_OK;
}

esp_err_t BalizamentoController::handleApiStatus(httpd_req_t *req) {
  if (!g_controller) { httpd_resp_send_404(req); return ESP_FAIL; }
  auto &c = *g_controller;

  int rssi; std::string ssid, ip, mac; bool wifi_ok;
  getWiFiInfo(rssi, ssid, ip, mac, wifi_ok);

  bool mqtt_ok = esphome::mqtt::global_mqtt_client &&
                  esphome::mqtt::global_mqtt_client->is_connected();

  StaticJsonDocument<1024> doc;
  doc["relay_on"] = c.relay_on_;
  doc["timer_active"] = c.timer_active_;
  if (c.timer_active_) {
    unsigned long el = (unsigned long)(esp_timer_get_time() / 1000) - c.timer_start_ms_;
    long rem = (c.timer_duration_ms_ > el) ? (c.timer_duration_ms_ - el) / 1000 : 0;
    doc["timer_remaining"] = rem;
    doc["timer_total"] = c.timer_duration_ms_ / 1000;
  } else {
    doc["timer_remaining"] = -1;
  }
  doc["wifi"] = wifi_ok;
  doc["mqtt"] = mqtt_ok;
  doc["tuya"] = c.tuya_ok_;
  doc["ip"] = ip;
  doc["ssid"] = ssid;
  doc["rssi"] = rssi;

  if (rssi >= -50) { doc["wifi_quality"] = "Excelente"; }
  else if (rssi >= -60) { doc["wifi_quality"] = "Bom"; }
  else if (rssi >= -67) { doc["wifi_quality"] = "Satisfatorio"; }
  else if (rssi >= -80) { doc["wifi_quality"] = "Fraco"; }
  else { doc["wifi_quality"] = "Inutilizavel"; }

  doc["uptime"] = (unsigned long)(esp_timer_get_time() / 1000000);
  doc["last_consumo"] = c.last_consumo_;
  doc["last_duration"] = c.last_duration_sec_;

  JsonObject en = doc.createNestedObject("energy");
  en["tensao"] = (c.current_tensao_ > 0) ? std::to_string(c.current_tensao_).substr(0,4) : "--";
  en["corrente"] = (c.current_corrente_ > 0) ? std::to_string(c.current_corrente_).substr(0,5) : "--";
  en["potencia"] = (c.current_potencia_ > 0) ? std::to_string(c.current_potencia_).substr(0,5) : "--";
  en["frequencia"] = (c.current_frequencia_ > 0) ? std::to_string(c.current_frequencia_).substr(0,4) : "--";
  en["energia"] = c.current_energy_;
  en["has_data"] = c.has_energy_data_;

  doc["saved_ssid"] = c.saved_config_.wifi_ssid;
  doc["saved_broker"] = c.saved_config_.mqtt_broker;
  doc["wifi_configured"] = strlen(c.saved_config_.wifi_ssid) > 0;
  doc["modo_manual"] = c.isManualMode();

  doc["timestamp"] = fmtTimestamp(::time(nullptr));

  std::string out;
  serializeJson(doc, out);
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, out.c_str(), out.length());
  return ESP_OK;
}

esp_err_t BalizamentoController::handleApiControl(httpd_req_t *req) {
  if (!g_controller) { httpd_resp_send_404(req); return ESP_FAIL; }
  char buf[512];
  int len = httpd_req_recv(req, buf, sizeof(buf) - 1);
  if (len <= 0) { httpd_resp_send_404(req); return ESP_FAIL; }
  buf[len] = 0;

  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, buf) != DeserializationError::Ok) {
    httpd_resp_send_404(req);
    return ESP_FAIL;
  }

  const char *action = doc["action"];
  if (!action) { httpd_resp_send_404(req); return ESP_FAIL; }

  if (strcmp(action, "on") == 0) {
    g_controller->handleBalCommand("BalOn", g_controller->current_energy_);
    float dur = doc["duration_min"] | 0;
    if (dur > 0) {
      g_controller->timer_duration_ms_ = (unsigned long)(dur * 60000);
      g_controller->timer_start_ms_ = (unsigned long)(esp_timer_get_time() / 1000);
      g_controller->timer_active_ = true;
    }
  } else if (strcmp(action, "off") == 0) {
    g_controller->handleBalCommand("BalOff", g_controller->current_energy_);
  }

  const char *resp = "{\"success\":true}";
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, resp, strlen(resp));
  return ESP_OK;
}

esp_err_t BalizamentoController::handleApiHistory(httpd_req_t *req) {
  if (!g_controller) { httpd_resp_send_404(req); return ESP_FAIL; }
  auto &c = *g_controller;

  StaticJsonDocument<8192> doc;
  JsonArray arr = doc.createNestedArray("history");
  for (const auto &h : c.history_) {
    JsonObject o = arr.createNestedObject();
    o["date"] = fmtDate(h.timestamp);
    o["start_time"] = fmtTime(h.timestamp - h.duration_sec);
    o["end_time"] = fmtTime(h.timestamp);
    o["duration_sec"] = h.duration_sec;
    o["energy_kwh"] = h.energy_kwh;
    o["completed"] = h.completed;
    o["has_energy"] = h.has_energy;
  }
  doc["count"] = c.history_.size();

  std::string out;
  serializeJson(doc, out);
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, out.c_str(), out.length());
  return ESP_OK;
}

esp_err_t BalizamentoController::handleApiOTA(httpd_req_t *req) {
  if (!g_controller) { httpd_resp_send_404(req); return ESP_FAIL; }
  char buf[512];
  int len = httpd_req_recv(req, buf, sizeof(buf) - 1);
  if (len <= 0) { httpd_resp_send_404(req); return ESP_FAIL; }
  buf[len] = 0;

  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, buf) != DeserializationError::Ok) {
    httpd_resp_send_404(req); return ESP_FAIL;
  }
  const char *url = doc["url"];
  if (!url || strlen(url) < 5) { httpd_resp_send_404(req); return ESP_FAIL; }

  const char *resp = "{\"success\":true}";
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, resp, strlen(resp));

  g_controller->performOTA(std::string(url));
  return ESP_OK;
}

esp_err_t BalizamentoController::handleApiRestart(httpd_req_t *req) {
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, "{\"success\":true}", 16);
  vTaskDelay(pdMS_TO_TICKS(100));
  esp_restart();
  return ESP_OK;
}

esp_err_t BalizamentoController::handleApiConfig(httpd_req_t *req) {
  if (!g_controller) { httpd_resp_send_404(req); return ESP_FAIL; }
  auto &c = *g_controller;

  if (req->method == HTTP_GET) {
    StaticJsonDocument<1024> doc;
    doc["wifi_ssid"] = c.saved_config_.wifi_ssid;
    doc["mqtt_broker"] = c.saved_config_.mqtt_broker;
    doc["mqtt_port"] = c.saved_config_.mqtt_port;
    doc["mqtt_username"] = c.saved_config_.mqtt_username;
    doc["mqtt_topic_suffix"] = strlen(c.saved_config_.mqtt_topic_suffix) > 0 ? c.saved_config_.mqtt_topic_suffix : "AeroClub Central";
    doc["timezone"] = strlen(c.saved_config_.timezone) > 0 ? c.saved_config_.timezone : "America/Sao_Paulo";

    std::string out;
    serializeJson(doc, out);
    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, out.c_str(), out.length());
    return ESP_OK;
  }

  char buf[1024];
  int len = httpd_req_recv(req, buf, sizeof(buf) - 1);
  if (len <= 0) { httpd_resp_send_404(req); return ESP_FAIL; }
  buf[len] = 0;

  StaticJsonDocument<1024> doc;
  if (deserializeJson(doc, buf) != DeserializationError::Ok) {
    httpd_resp_send_404(req);
    return ESP_FAIL;
  }

  SavedConfig cfg = {};
  const char *ssid = doc["wifi_ssid"];
  const char *pass = doc["wifi_password"];
  const char *broker = doc["mqtt_broker"];
  int port = doc["mqtt_port"] | 1883;
  const char *muser = doc["mqtt_username"];
  const char *mpass = doc["mqtt_password"];

  if (ssid) strncpy(cfg.wifi_ssid, ssid, sizeof(cfg.wifi_ssid) - 1);
  if (pass) strncpy(cfg.wifi_password, pass, sizeof(cfg.wifi_password) - 1);
  if (broker) strncpy(cfg.mqtt_broker, broker, sizeof(cfg.mqtt_broker) - 1);
  cfg.mqtt_port = (uint16_t)port;
  if (muser) strncpy(cfg.mqtt_username, muser, sizeof(cfg.mqtt_username) - 1);
  if (mpass) strncpy(cfg.mqtt_password, mpass, sizeof(cfg.mqtt_password) - 1);

  const char *suffix = doc["mqtt_topic_suffix"];
  const char *tz = doc["timezone"];
  if (suffix) strncpy(cfg.mqtt_topic_suffix, suffix, sizeof(cfg.mqtt_topic_suffix) - 1);
  if (tz) strncpy(cfg.timezone, tz, sizeof(cfg.timezone) - 1);

  c.saveConfig(cfg);

  bool needs_reboot = true;
  StaticJsonDocument<128> resp;
  resp["success"] = true;
  resp["needs_reboot"] = needs_reboot;

  std::string out;
  serializeJson(resp, out);
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, out.c_str(), out.length());
  return ESP_OK;
}

// ==================== WIFI SCAN ====================
esp_err_t BalizamentoController::handleApiScan(httpd_req_t *req) {
  if (!g_controller) { httpd_resp_send_404(req); return ESP_FAIL; }

  ESP_LOGI(TAG, "Iniciando scan WiFi...");

  wifi_mode_t mode;
  esp_wifi_get_mode(&mode);
  ESP_LOGI(TAG, "Modo WiFi atual: %d", mode);

  if (mode != WIFI_MODE_STA && mode != WIFI_MODE_APSTA) {
    ESP_LOGI(TAG, "Alterando modo para APSTA");
    ESP_ERROR_CHECK_WITHOUT_ABORT(esp_wifi_set_mode(WIFI_MODE_APSTA));
    delay(200);
  }

  // Limpar scan anterior
  esp_wifi_scan_stop();

  wifi_scan_config_t conf = {};
  conf.scan_type = WIFI_SCAN_TYPE_ACTIVE;
  conf.scan_time.active.min = 200;
  conf.scan_time.active.max = 500;
  conf.show_hidden = true;

  esp_err_t err = esp_wifi_scan_start(&conf, false);
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "Falha no scan: %s", esp_err_to_name(err));
    const char *resp = "{\"error\":\"scan_failed\"}";
    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, resp, strlen(resp));
    return ESP_OK;
  }

  uint16_t count = 0;
  for (int retry = 0; retry < 50; retry++) {
    delay(100);
    esp_wifi_scan_get_ap_num(&count);
    if (count > 0) break;
  }
  ESP_LOGI(TAG, "Scan concluido: %d redes", count);
  if (count > 50) count = 50;

  JsonDocument doc;
  JsonArray nets = doc["networks"].to<JsonArray>();

  if (count > 0) {
    wifi_ap_record_t *recs = (wifi_ap_record_t *)malloc(sizeof(wifi_ap_record_t) * count);
    if (recs) {
      esp_wifi_scan_get_ap_records(&count, recs);
      for (int i = 0; i < count; i++) {
        if (strlen((char *)recs[i].ssid) == 0) continue;
        JsonObject net = nets.add<JsonObject>();
        net["ssid"] = (char *)recs[i].ssid;
        net["rssi"] = recs[i].rssi;
        net["channel"] = recs[i].primary;
        net["auth"] = (recs[i].authmode == WIFI_AUTH_OPEN) ? "aberta" : "protegida";
      }
      free(recs);
    }
  }

  std::string out;
  serializeJson(doc, out);
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, out.c_str(), out.length());
  return ESP_OK;
}

esp_err_t BalizamentoController::handleApiSchedules(httpd_req_t *req) {
  if (!g_controller) { httpd_resp_send_404(req); return ESP_FAIL; }
  auto &c = *g_controller;

  StaticJsonDocument<4096> doc;
  JsonArray arr = doc.createNestedArray("schedules");
  for (const auto &s : c.schedule_queue_) {
    JsonObject o = arr.createNestedObject();
    o["id"] = s.id;
    o["start_timestamp"] = s.start_timestamp;
    o["end_timestamp"] = s.end_timestamp;
    o["duration_sec"] = s.duration_sec;
    o["executed"] = s.executed;
    if (s.start_timestamp >= 100000) o["start"] = fmtDate(s.start_timestamp) + " " + fmtTime(s.start_timestamp);
    if (s.end_timestamp >= 100000) o["end"] = fmtDate(s.end_timestamp) + " " + fmtTime(s.end_timestamp);
  }
  doc["count"] = c.schedule_queue_.size();

  std::string out;
  serializeJson(doc, out);
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, out.c_str(), out.length());
  return ESP_OK;
}

// ==================== TIMER ====================
void BalizamentoController::checkTimer() {
  if (!timer_active_) return;
  unsigned long now = (unsigned long)(esp_timer_get_time() / 1000);
  unsigned long elapsed = now - timer_start_ms_;
  if (elapsed >= timer_duration_ms_) {
    ESP_LOGI(TAG, "Timer expirado");
    timer_active_ = false;
    finishActivation(true);
  }
}

void BalizamentoController::finishActivation(bool completed) {
  if (!relay_on_) { timer_active_ = false; return; }
  energy_end_kwh_ = current_energy_;
  gpio_set_level(RELAY_PIN, 0);
  relay_on_ = false;

  unsigned long dur_ms = timer_active_ ? ((unsigned long)(esp_timer_get_time() / 1000) - timer_start_ms_) : timer_duration_ms_;
  unsigned long dur_sec = (dur_ms > 0) ? dur_ms / 1000 : 1;

  float diff = 0;
  bool he = has_energy_data_ && energy_start_kwh_ > 0;
  if (he && energy_end_kwh_ > energy_start_kwh_) diff = energy_end_kwh_ - energy_start_kwh_;

  last_consumo_ = diff;
  last_duration_sec_ = dur_sec;
  addHistory(dur_sec, diff, completed, he);
  publishConsumption(diff, dur_sec);
  publishStatus();
  tuya_ok_ = false; // simplified: no Tuya DP report in IDF version
  timer_active_ = false;
  ESP_LOGI(TAG, "Ativacao finalizada - %lus %.3fkWh", dur_sec, diff);
}

// ==================== COMANDOS ====================
void BalizamentoController::handleBalCommand(const std::string &payload, float energia) {
  mqtt_received_count_++;
  ESP_LOGI(TAG, "MQTT RECEBIDO [%s]: %s", bal_write_topic_.c_str(), payload.c_str());
  std::string cmd;
  StaticJsonDocument<512> doc;
  if (deserializeJson(doc, payload) == DeserializationError::Ok && doc.is<JsonObject>()) {
    const char *c = doc["comando"]; if (c) cmd = c;
    if (doc.containsKey("agendamento")) {
      float dur = doc["agendamento"]["duracao_minutos"] | 0;
      if (dur > 0) {
        timer_duration_ms_ = (unsigned long)(dur * 60000);
        timer_active_ = true;
      }
    }
  } else {
    cmd = payload;
  }

  last_command_ = cmd;

  if (cmd == "BalOn") {
    energy_start_kwh_ = energia;
    gpio_set_level(RELAY_PIN, 1);
    relay_on_ = true;
    timer_start_ms_ = (unsigned long)(esp_timer_get_time() / 1000);
    if (timer_duration_ms_ == 0) { timer_duration_ms_ = 600000; timer_active_ = true; }
    activation_count_++;
    time_t t = ::time(nullptr);
    struct tm *ti = localtime(&t);
    char buf[25];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", ti);
    last_activation_timestamp_ = buf;
    publishStatus();
  } else if (cmd == "BalOff") {
    finishActivation(false);
    } else if (cmd == "RequestHeartbeat") {
      publishHeartbeat();
    } else if (cmd == "AgendarBalizamento") {
      if (doc.containsKey("agendamento")) {
        JsonObject ag = doc["agendamento"];
        const char *data_str = ag["data"];
        const char *hora_inicio = ag["hora_inicio"];
        const char *hora_fim = ag["hora_fim"];
        uint32_t dur = ag["duracao_segundos"] | 0;
        uint32_t sched_id = ag["id"] | 0;
        if (data_str && hora_inicio && hora_fim && sched_id > 0) {
          time_t start_ts = parseScheduleDateTime(data_str, hora_inicio);
          time_t end_ts = parseScheduleDateTime(data_str, hora_fim);
          ESP_LOGI(TAG, "Agendar: id=%u start_ts=%lld end_ts=%lld now=%lld", sched_id, (long long)start_ts, (long long)end_ts, (long long)::time(nullptr));
          if (start_ts > 0 && end_ts > start_ts && end_ts > ::time(nullptr)) {
            bool found = false;
            for (auto &s : schedule_queue_) {
              if (s.id == sched_id) {
                s.start_timestamp = (uint32_t)start_ts;
                s.end_timestamp = (uint32_t)end_ts;
                s.duration_sec = dur;
                s.executed = false;
                found = true;
                break;
              }
            }
            if (!found && schedule_queue_.size() < MAX_SCHEDULES) {
              ScheduledEvent se;
              se.id = sched_id;
              se.start_timestamp = (uint32_t)start_ts;
              se.end_timestamp = (uint32_t)end_ts;
              se.duration_sec = dur;
              se.executed = false;
              schedule_queue_.push_back(se);
            }
            if (found || (!found && schedule_queue_.size() < MAX_SCHEDULES)) {
              saveSchedules();
              ESP_LOGI(TAG, "Agendamento %u agendado: inicio=%u, fim=%u, duracao=%us", sched_id, (uint32_t)start_ts, (uint32_t)end_ts, dur);
              publishScheduleStatus(sched_id, "AgendamentoConfirmado", "agendado");
            }
          }
        }
      }
    } else if (cmd == "CancelarAgendamento") {
      uint32_t cancel_id = doc["agendamento"]["id"] | 0;
      if (cancel_id > 0) {
        for (auto it = schedule_queue_.begin(); it != schedule_queue_.end(); ++it) {
          if (it->id == cancel_id) {
            if (it->executed && relay_on_) {
              finishActivation(false);
            }
            schedule_queue_.erase(it);
            saveSchedules();
            ESP_LOGI(TAG, "Agendamento %u removido", cancel_id);
            break;
          }
        }
      }
    } else if (cmd == "UpdateFirmware") {
    const char *url = doc["url"];
    if (url && strlen(url) > 5) {
      ESP_LOGI(TAG, "Iniciando OTA via MQTT: %s", url);
      performOTA(std::string(url));
    } else {
      ESP_LOGE(TAG, "UpdateFirmware sem URL valida");
    }
  }
}

// ==================== MQTT ====================
void BalizamentoController::publishStatus() {
  if (!esphome::mqtt::global_mqtt_client) return;
  StaticJsonDocument<256> doc;
  doc["comando"] = relay_on_ ? "BalOn" : "BalOff";
  doc["estado"] = relay_on_;
  doc["timestamp"] = fmtTimestamp(::time(nullptr));
  std::string out;
  serializeJson(doc, out);
  mqtt_published_count_++;
  ESP_LOGI(TAG, "MQTT ENVIO [%s]: %s", bal_read_topic_.c_str(), out.c_str());
  esphome::mqtt::global_mqtt_client->publish(bal_read_topic_, out);
}

void BalizamentoController::publishConsumption(float diff_kwh, unsigned long dur_sec) {
  if (!esphome::mqtt::global_mqtt_client) return;
  bool connected = esphome::mqtt::global_mqtt_client->is_connected();
  if (!connected) {
    has_pending_consumption_ = true;
    pending_consumption_kwh_ = diff_kwh;
    pending_duration_sec_ = dur_sec;
    ESP_LOGW(TAG, "MQTT desconectado, consumo pendente salvo");
    return;
  }
  has_pending_consumption_ = false;
  StaticJsonDocument<512> doc;
  doc["comando"] = "ConsumoBalizamento";
  doc["energia_inicial_kwh"] = energy_start_kwh_;
  doc["energia_final_kwh"] = energy_end_kwh_;
  doc["consumo_kwh"] = diff_kwh;
  doc["duracao_segundos"] = dur_sec;
  doc["duracao_minutos"] = dur_sec / 60.0;
  doc["timestamp"] = fmtTimestamp(::time(nullptr));
  std::string out;
  serializeJson(doc, out);
  mqtt_published_count_++;
  ESP_LOGI(TAG, "MQTT ENVIO [%s]: %s", bal_read_topic_.c_str(), out.c_str());
  esphome::mqtt::global_mqtt_client->publish(bal_read_topic_, out);
}

void BalizamentoController::publishScheduleStatus(uint32_t id, const char *comando, const char *status) {
  if (!esphome::mqtt::global_mqtt_client) return;
  StaticJsonDocument<256> doc;
  doc["comando"] = comando;
  JsonObject ag = doc.createNestedObject("agendamento");
  ag["id"] = id;
  ag["status"] = status;
  ag["data_hora"] = fmtTimestamp(::time(nullptr));
  std::string out;
  serializeJson(doc, out);
  mqtt_published_count_++;
  ESP_LOGI(TAG, "MQTT ENVIO [%s]: %s", bal_read_topic_.c_str(), out.c_str());
  esphome::mqtt::global_mqtt_client->publish(bal_read_topic_, out);
}

void BalizamentoController::publishEnergyRegisters() {
  if (!esphome::mqtt::global_mqtt_client) return;
  StaticJsonDocument<2048> doc;
  doc["topic"] = sdm_read_topic_;
  doc["payload"] = "ReadRegistersEnergy";
  doc["aeroclube_id"] = 1;
  doc["aeroclube_nome"] = saved_config_.mqtt_topic_suffix;
  doc["confirmado"] = true;
  doc["timestamp"] = fmtTimestamp(::time(nullptr));
  JsonObject eq = doc.createNestedObject("equipamento");
  eq["fabricante"] = "Eastron";
  eq["modelo"] = "SDM120";

  std::string mac; int rssi; std::string ssid, ip; bool wk;
  getWiFiInfo(rssi, ssid, ip, mac, wk);
  ESP_LOGI(TAG, "WiFi conectado - SSID: %s, IP: %s", ssid.c_str(), ip.c_str());
  eq["numero_serie"] = mac;
  eq["firmware"] = "1.0.0";
  doc["status"] = "OK";

  JsonObject regs = doc.createNestedObject("registradores");
  auto addReg = [&](const char *addr, const char *desc, float val, const char *unit) {
    regs[addr]["descricao"] = desc;
    regs[addr]["valor"] = (val > 0) ? val : 0;
    regs[addr]["unidade"] = unit;
  };
  addReg("0000", "Tensao", current_tensao_, "V");
  addReg("0006", "Corrente", current_corrente_, "A");
  addReg("000C", "Potencia Ativa", current_potencia_, "W");
  addReg("0012", "Potencia Aparente", 0, "VA");
  addReg("0018", "Potencia Reativa", 0, "VAr");
  addReg("001E", "Frequencia", current_frequencia_, "Hz");
  addReg("0036", "Fator Potencia", 0, "");
  addReg("0046", "Energia Importada", current_energy_, "kWh");

  std::string out;
  serializeJson(doc, out);
  mqtt_published_count_++;
  ESP_LOGI(TAG, "MQTT ENVIO [%s]: %s", sdm_read_topic_.c_str(), out.c_str());
  esphome::mqtt::global_mqtt_client->publish(sdm_read_topic_, out);
}

// ==================== HEARTBEAT TRACKING ====================
void BalizamentoController::onWiFiConnected() {
  wifi_reconnect_count_++;
  ESP_LOGI(TAG, "WiFi reconectado (#%d)", wifi_reconnect_count_);
  publishHeartbeat();
}

void BalizamentoController::onMqttConnected() {
  last_mqtt_connect_ms_ = (unsigned long)(esp_timer_get_time() / 1000);
  last_mqtt_connect_time_ = ::time(nullptr);
  mqtt_was_connected_ = true;
  ESP_LOGI(TAG, "MQTT reconectado");
  // Subscrever topicos com sufixo configurado
  if (esphome::mqtt::global_mqtt_client) {
    esphome::mqtt::global_mqtt_client->subscribe(
        bal_write_topic_, [this](const std::string &topic, const std::string &payload) {
          float energia_atual = current_energy_;
          handleBalCommand(payload, energia_atual);
        }, 0);
    esphome::mqtt::global_mqtt_client->subscribe(
        sdm_write_topic_, [this](const std::string &topic, const std::string &payload) {
          ::sdm120_on_message(payload);
        }, 0);
    ESP_LOGI(TAG, "Inscrito em: %s / %s", bal_write_topic_.c_str(), sdm_write_topic_.c_str());
  }
  publishHeartbeat();

  // Reenviar consumo pendente se houver
  if (has_pending_consumption_) {
    ESP_LOGI(TAG, "Reenviando consumo pendente: %.3fkWh %lus", pending_consumption_kwh_, pending_duration_sec_);
    float saved_diff = pending_consumption_kwh_;
    unsigned long saved_dur = pending_duration_sec_;
    has_pending_consumption_ = false;
    publishConsumption(saved_diff, saved_dur);
  }
}

void BalizamentoController::onMqttDisconnected() {
  mqtt_was_connected_ = false;
  ESP_LOGW(TAG, "MQTT desconectado");
}

// ==================== HEARTBEAT ====================
void BalizamentoController::publishHeartbeat() {
  if (!esphome::mqtt::global_mqtt_client) return;
  if (!esphome::mqtt::global_mqtt_client->is_connected()) return;

  if (!heartbeat_initialized_) {
    heartbeat_initialized_ = true;
    // Cache app SHA256 once
    char sha256_buf[65] = {0};
    esp_ota_get_app_elf_sha256(sha256_buf, sizeof(sha256_buf));
    app_sha256_ = sha256_buf;
    // Load restart count from NVS
    nvs_handle_t h;
    if (nvs_open("heartbeat", NVS_READONLY, &h) == ESP_OK) {
      int32_t v = 0;
      nvs_get_i32(h, "restarts", &v);
      restart_count_ = (int)v;
      nvs_close(h);
    }
  }

  int rssi; std::string ssid, ip, mac; bool wifi_ok;
  getWiFiInfo(rssi, ssid, ip, mac, wifi_ok);

  uint32_t uptime_sec = (uint32_t)(esp_timer_get_time() / 1000000);
  uint32_t heap_free = (uint32_t)esp_get_free_heap_size();
  uint32_t cpu_mhz = ESP.getCpuFreqMHz();
  esp_reset_reason_t reset_reason = esp_reset_reason();

  const char *reset_str = "Desconhecido";
  switch (reset_reason) {
    case ESP_RST_POWERON: reset_str = "Power On"; break;
    case ESP_RST_EXT: reset_str = "External Pin"; break;
    case ESP_RST_SW: reset_str = "Software Restart"; break;
    case ESP_RST_PANIC: reset_str = "Panic"; break;
    case ESP_RST_INT_WDT: reset_str = "Interrupt WDT"; break;
    case ESP_RST_TASK_WDT: reset_str = "Task WDT"; break;
    case ESP_RST_WDT: reset_str = "Watchdog"; break;
    case ESP_RST_DEEPSLEEP: reset_str = "Deep Sleep Wake"; break;
    case ESP_RST_BROWNOUT: reset_str = "Brownout"; break;
    case ESP_RST_SDIO: reset_str = "SDIO"; break;
    default: break;
  }

  // Flash free - use data partition info
  uint32_t flash_free = 0;
  const esp_partition_t *part = esp_partition_find_first(ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_ANY, NULL);
  if (part) {
    flash_free = part->size;
  }

  // Internal temperature via ESP32-Sensor
  float internal_temp = NAN;
  esp_err_t temp_err = ESP_FAIL;
#if CONFIG_IDF_TARGET_ESP32S2 || CONFIG_IDF_TARGET_ESP32S3 || CONFIG_IDF_TARGET_ESP32C3 || CONFIG_IDF_TARGET_ESP32C6
  temp_err = esp_temp_sens_read_celsius(&internal_temp);
#else
  (void)temp_err;
#endif

  // Gateway and DNS
  std::string gateway = "Desconhecido";
  std::string dns = "Desconhecido";
  esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
  if (netif) {
    esp_netif_ip_info_t info;
    if (esp_netif_get_ip_info(netif, &info) == ESP_OK) {
      char buf[16];
      esp_ip4addr_ntoa(&info.gw, buf, sizeof(buf));
      gateway = buf;
    }
    esp_netif_dns_info_t dns_info;
    if (esp_netif_get_dns_info(netif, ESP_NETIF_DNS_MAIN, &dns_info) == ESP_OK) {
      char buf[16];
      esp_ip4addr_ntoa(&dns_info.ip.u_addr.ip4, buf, sizeof(buf));
      dns = buf;
    }
  }

  // WiFi quality %
  int wifi_quality = 0;
  if (rssi <= -100) wifi_quality = 0;
  else if (rssi >= -50) wifi_quality = 100;
  else wifi_quality = 2 * (rssi + 100);

  DynamicJsonDocument doc(4096);

  JsonObject device = doc.createNestedObject("device");
  device["nome"] = esphome::App.get_friendly_name().c_str();
  device["modelo"] = "ESP32";
  device["serial"] = DEVICE_SERIAL;
  device["hardware"] = DEVICE_HARDWARE;
  device["mac"] = mac;
  device["ip"] = ip;
  device["hostname"] = esphome::App.get_name().c_str();
  device["esphome_version"] = ESPHOME_VERSION;

  JsonObject firmware = doc.createNestedObject("firmware");
  firmware["versao"] = FIRMWARE_VERSION;
  firmware["arquivo_bin"] = FIRMWARE_BIN;
  firmware["build_date"] = std::string(__DATE__) + " " + std::string(__TIME__);
  firmware["md5"] = app_sha256_;
  firmware["ota_channel"] = FIRMWARE_OTA_CHANNEL;
  firmware["ota_disponivel"] = false;

  JsonObject wifi_obj = doc.createNestedObject("wifi");
  wifi_obj["ssid"] = wifi_ok ? ssid : "Desconhecido";
  wifi_obj["rssi"] = rssi;
  wifi_obj["qualidade"] = wifi_quality;
  wifi_obj["ip"] = ip;
  wifi_obj["gateway"] = gateway;
  wifi_obj["dns"] = dns;
  wifi_obj["mac"] = mac;
  wifi_obj["reconexoes"] = wifi_reconnect_count_;

  bool mqtt_ok = esphome::mqtt::global_mqtt_client &&
                  esphome::mqtt::global_mqtt_client->is_connected();
  JsonObject mqtt_obj = doc.createNestedObject("mqtt");
  mqtt_obj["broker"] = strlen(saved_config_.mqtt_broker) > 0 ? saved_config_.mqtt_broker : "broker.emqx.io";
  mqtt_obj["status"] = mqtt_ok ? "Conectado" : "Desconectado";
  mqtt_obj["mensagens_publicadas"] = mqtt_published_count_;
  mqtt_obj["mensagens_recebidas"] = mqtt_received_count_;
  if (last_mqtt_connect_time_ > 0) {
    struct tm *ti = localtime(&last_mqtt_connect_time_);
    char buf[25];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", ti);
    mqtt_obj["ultima_reconexao"] = buf;
  } else {
    mqtt_obj["ultima_reconexao"] = nullptr;
  }

  JsonObject bal = doc.createNestedObject("balizamento");
  bal["status"] = relay_on_ ? "Ativo" : "Inativo";
  bal["gpio"] = RELAY_PIN;
  bal["ultimo_comando"] = last_command_.empty() ? "Nenhum" : last_command_;
  if (last_activation_timestamp_.empty()) {
    bal["ultimo_acionamento"] = nullptr;
  } else {
    bal["ultimo_acionamento"] = last_activation_timestamp_;
  }
  bal["tempo_ligado_segundos"] = total_on_time_ms_ / 1000;
  bal["contador_acionamentos"] = activation_count_;
  bal["modo_manual"] = isManualMode();

  JsonObject sistema = doc.createNestedObject("sistema");
  sistema["uptime_segundos"] = uptime_sec;
  sistema["reinicios"] = restart_count_;
  sistema["motivo_ultimo_reset"] = reset_str;
  sistema["heap_livre"] = heap_free;
  sistema["cpu_mhz"] = cpu_mhz;
  if (!std::isnan(internal_temp)) {
    sistema["temperatura_interna"] = (double)internal_temp;
  } else {
    sistema["temperatura_interna"] = nullptr;
  }
  sistema["flash_livre"] = flash_free;

  time_t now = ::time(nullptr);
  struct tm *ti = localtime(&now);
  char ts_buf[25];
  strftime(ts_buf, sizeof(ts_buf), "%Y-%m-%dT%H:%M:%S", ti);
  doc["timestamp"] = ts_buf;

  std::string out;
  serializeJson(doc, out);
  mqtt_published_count_++;
  ESP_LOGI(TAG, "MQTT ENVIO [%s]", heartbeat_topic_.c_str());
  esphome::mqtt::global_mqtt_client->publish(heartbeat_topic_, out);
}

// ==================== HISTORICO ====================
void BalizamentoController::loadHistory() {
  history_.clear();
  esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_handle_);
  if (err != ESP_OK) return;
  int32_t count = 0;
  nvs_get_i32(nvs_handle_, "count", &count);
  if (count > MAX_HISTORY) count = MAX_HISTORY;
  for (int32_t i = 0; i < count; i++) {
    char key[16]; snprintf(key, sizeof(key), "rec_%ld", (long)i);
    size_t sz = 0;
    if (nvs_get_blob(nvs_handle_, key, NULL, &sz) != ESP_OK || sz != sizeof(HistoryEntry)) continue;
    HistoryEntry e;
    if (nvs_get_blob(nvs_handle_, key, &e, &sz) == ESP_OK) {
      history_.push_back(e);
    }
  }
  nvs_close(nvs_handle_);
  ESP_LOGI(TAG, "Historico: %d registros", history_.size());
}

void BalizamentoController::saveHistory() {
  esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_handle_);
  if (err != ESP_OK) return;
  int32_t count = (int32_t)history_.size();
  nvs_set_i32(nvs_handle_, "count", count);
  for (int32_t i = 0; i < count && i < MAX_HISTORY; i++) {
    char key[16]; snprintf(key, sizeof(key), "rec_%ld", (long)i);
    nvs_set_blob(nvs_handle_, key, &history_[i], sizeof(HistoryEntry));
  }
  nvs_commit(nvs_handle_);
  nvs_close(nvs_handle_);
}

// ==================== AGENDA ====================
time_t BalizamentoController::parseScheduleDateTime(const char *date, const char *time_str) {
  struct tm tm = {};
  int d, m, y, h, min, s = 0;
  if (sscanf(date, "%d/%d/%d", &d, &m, &y) != 3) return 0;
  if (sscanf(time_str, "%d:%d:%d", &h, &min, &s) < 2) return 0;
  tm.tm_mday = d;
  tm.tm_mon = m - 1;
  tm.tm_year = y - 1900;
  tm.tm_hour = h;
  tm.tm_min = min;
  tm.tm_sec = s;
  tm.tm_isdst = -1;
  time_t result = mktime(&tm);
  ESP_LOGI(TAG, "parseScheduleDateTime: data=%s hora=%s -> %lld", date, time_str, (long long)result);
  return result;
}

void BalizamentoController::loadSchedules() {
  schedule_queue_.clear();
  nvs_handle_t h;
  if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &h) != ESP_OK) return;
  int32_t count = 0;
  nvs_get_i32(h, "sched_count", &count);
  if (count > MAX_SCHEDULES) count = MAX_SCHEDULES;
  for (int32_t i = 0; i < count; i++) {
    char key[16]; snprintf(key, sizeof(key), "sched_%ld", (long)i);
    size_t sz = 0;
    if (nvs_get_blob(h, key, NULL, &sz) != ESP_OK || sz != sizeof(ScheduledEvent)) continue;
    ScheduledEvent e;
    if (nvs_get_blob(h, key, &e, &sz) == ESP_OK) {
      schedule_queue_.push_back(e);
    }
  }
  nvs_close(h);
  cleanupSchedules();
  ESP_LOGI(TAG, "Agenda: %d eventos", schedule_queue_.size());
}

void BalizamentoController::saveSchedules() {
  nvs_handle_t h;
  if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) return;
  int32_t count = (int32_t)schedule_queue_.size();
  nvs_set_i32(h, "sched_count", count);
  for (int32_t i = 0; i < count && i < MAX_SCHEDULES; i++) {
    char key[16]; snprintf(key, sizeof(key), "sched_%ld", (long)i);
    nvs_set_blob(h, key, &schedule_queue_[i], sizeof(ScheduledEvent));
  }
  nvs_commit(h);
  nvs_close(h);
}

void BalizamentoController::cleanupSchedules() {
  time_t now = ::time(nullptr);
  bool changed = false;
  for (auto it = schedule_queue_.begin(); it != schedule_queue_.end(); ) {
    if ((time_t)it->end_timestamp < now) {
      it = schedule_queue_.erase(it);
      changed = true;
    } else {
      ++it;
    }
  }
  if (changed) saveSchedules();
}

void BalizamentoController::checkSchedules() {
  time_t now = ::time(nullptr);
  if (now < 100000) return;

  for (auto &s : schedule_queue_) {
    if (!s.executed && now >= (time_t)s.start_timestamp && now < (time_t)s.end_timestamp) {
      if (!relay_on_) {
        ESP_LOGI(TAG, "Agenda %u: iniciando", s.id);
        StaticJsonDocument<256> json_cmd;
        json_cmd["comando"] = "BalOn";
        JsonObject ag = json_cmd.createNestedObject("agendamento");
        ag["duracao_minutos"] = s.duration_sec / 60.0;
        std::string payload;
        serializeJson(json_cmd, payload);
        handleBalCommand(payload, current_energy_);
      }
      s.executed = true;
      saveSchedules();
      publishScheduleStatus(s.id, "AgendamentoAndamento", "em_andamento");
    }
    if (s.executed && now >= (time_t)s.end_timestamp) {
      ESP_LOGI(TAG, "Agenda %u: finalizando", s.id);
      finishActivation(true);
      publishScheduleStatus(s.id, "AgendamentoFinalizado", "finalizado");
    }
  }
  cleanupSchedules();
}

void BalizamentoController::addHistory(uint32_t dur, float energy, bool completed, bool has_energy) {
  HistoryEntry e;
  e.timestamp = (uint32_t)::time(nullptr);
  e.duration_sec = dur;
  e.energy_kwh = energy;
  e.completed = completed;
  e.has_energy = has_energy;
  history_.insert(history_.begin(), e);
  if (history_.size() > MAX_HISTORY) history_.pop_back();
  saveHistory();
}

// ==================== OTA ====================
void BalizamentoController::performOTA(const std::string &url) {
  ESP_LOGI(TAG, "OTA: %s", url.c_str());

  esp_http_client_config_t cfg = {};
  cfg.url = url.c_str();
  cfg.timeout_ms = 30000;
  cfg.keep_alive_enable = false;

  esp_http_client_handle_t client = esp_http_client_init(&cfg);
  esp_err_t err = esp_http_client_open(client, 0);
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "HTTP open falhou: %s", esp_err_to_name(err));
    esp_http_client_cleanup(client);
    return;
  }

  int content_len = esp_http_client_fetch_headers(client);
  if (content_len <= 0) {
    ESP_LOGE(TAG, "Content-Length invalido: %d", content_len);
    esp_http_client_cleanup(client);
    return;
  }

  const esp_partition_t *update_part = esp_ota_get_next_update_partition(NULL);
  if (!update_part) {
    ESP_LOGE(TAG, "Nenhuma particao OTA");
    esp_http_client_cleanup(client);
    return;
  }

  esp_ota_handle_t update_handle;
  err = esp_ota_begin(update_part, content_len, &update_handle);
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "esp_ota_begin: %s", esp_err_to_name(err));
    esp_http_client_cleanup(client);
    return;
  }

  uint8_t buf[1024];
  int written = 0;
  while (written < content_len) {
    int r = esp_http_client_read(client, (char *)buf, sizeof(buf));
    if (r <= 0) {
      ESP_LOGE(TAG, "Leitura HTTP: %d", r);
      break;
    }
    err = esp_ota_write(update_handle, buf, r);
    if (err != ESP_OK) {
      ESP_LOGE(TAG, "esp_ota_write: %s", esp_err_to_name(err));
      break;
    }
    written += r;
  }

  esp_http_client_cleanup(client);

  if (written == content_len) {
    err = esp_ota_end(update_handle);
    if (err == ESP_OK) {
      err = esp_ota_set_boot_partition(update_part);
      if (err == ESP_OK) {
        ESP_LOGI(TAG, "OTA OK! %d bytes. Reiniciando...", written);
        vTaskDelay(pdMS_TO_TICKS(500));
        esp_restart();
      }
    }
  } else {
    esp_ota_abort(update_handle);
    ESP_LOGE(TAG, "OTA falhou: %d/%d bytes", written, content_len);
  }
}

// ==================== TUYA ====================
void BalizamentoController::initTuya() {
  if (g_tuya_pid.empty() || g_tuya_did.empty()) {
    ESP_LOGW(TAG, "Tuya nao configurado");
    return;
  }
  ESP_LOGI(TAG, "Tuya placeholder - endpoint: %s", g_tuya_reg.c_str());
  last_tuya_reconnect_ = 0;
}

void BalizamentoController::checkTuya() {
  // Tuya MQTT with TLS requires significant setup
  // Placeholder for future implementation
}

std::string BalizamentoController::tuyaHmacSha256(const std::string &key, const std::string &msg) {
  uint8_t hmac[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
  mbedtls_md_hmac_starts(&ctx, (const uint8_t *)key.data(), key.length());
  mbedtls_md_hmac_update(&ctx, (const uint8_t *)msg.data(), msg.length());
  mbedtls_md_hmac_finish(&ctx, hmac);
  mbedtls_md_free(&ctx);

  char hex[65];
  for (int i = 0; i < 32; i++) snprintf(hex + (i * 2), 3, "%02x", hmac[i]);
  hex[64] = 0;
  return std::string(hex);
}

// ==================== CONFIG NVS ====================
void BalizamentoController::loadSavedConfig() {
  SavedConfig cfg = {};
  esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READONLY, &nvs_handle_);
  if (err != ESP_OK) { saved_config_ = cfg; return; }

  size_t sz;
  sz = sizeof(cfg.wifi_ssid);
  nvs_get_str(nvs_handle_, "wifi_ssid", cfg.wifi_ssid, &sz);
  sz = sizeof(cfg.wifi_password);
  nvs_get_str(nvs_handle_, "wifi_pass", cfg.wifi_password, &sz);
  sz = sizeof(cfg.mqtt_broker);
  nvs_get_str(nvs_handle_, "mqtt_broker", cfg.mqtt_broker, &sz);
  uint16_t port = 0;
  nvs_get_u16(nvs_handle_, "mqtt_port", &port);
  cfg.mqtt_port = port;
  sz = sizeof(cfg.mqtt_username);
  nvs_get_str(nvs_handle_, "mqtt_user", cfg.mqtt_username, &sz);
  sz = sizeof(cfg.mqtt_password);
  nvs_get_str(nvs_handle_, "mqtt_pass", cfg.mqtt_password, &sz);
  sz = sizeof(cfg.mqtt_topic_suffix);
  nvs_get_str(nvs_handle_, "topic_suf", cfg.mqtt_topic_suffix, &sz);
  sz = sizeof(cfg.timezone);
  nvs_get_str(nvs_handle_, "timezone", cfg.timezone, &sz);

  nvs_close(nvs_handle_);
  saved_config_ = cfg;
  ESP_LOGI(TAG, "Config carregada - WiFi: %s, MQTT: %s", cfg.wifi_ssid, cfg.mqtt_broker);
}

void BalizamentoController::saveConfig(const SavedConfig &cfg) {
  esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_handle_);
  if (err != ESP_OK) return;

  nvs_set_str(nvs_handle_, "wifi_ssid", cfg.wifi_ssid);
  nvs_set_str(nvs_handle_, "wifi_pass", cfg.wifi_password);
  nvs_set_str(nvs_handle_, "mqtt_broker", cfg.mqtt_broker);
  nvs_set_u16(nvs_handle_, "mqtt_port", cfg.mqtt_port);
  nvs_set_str(nvs_handle_, "mqtt_user", cfg.mqtt_username);
  nvs_set_str(nvs_handle_, "mqtt_pass", cfg.mqtt_password);
  nvs_set_str(nvs_handle_, "topic_suf", cfg.mqtt_topic_suffix);
  nvs_set_str(nvs_handle_, "timezone", cfg.timezone);
  nvs_commit(nvs_handle_);
  nvs_close(nvs_handle_);

  saved_config_ = cfg;
  buildTopics();
  ESP_LOGI(TAG, "Config salva - WiFi: %s, MQTT: %s:%d, Sufixo: %s", cfg.wifi_ssid, cfg.mqtt_broker, cfg.mqtt_port, cfg.mqtt_topic_suffix);
}

void BalizamentoController::reconnectWiFi() {
  if (strlen(saved_config_.wifi_ssid) == 0) return;
  ESP_LOGI(TAG, "Reconectando WiFi para %s", saved_config_.wifi_ssid);

  wifi_config_t wifi_cfg = {};
  strncpy((char*)wifi_cfg.sta.ssid, saved_config_.wifi_ssid, sizeof(wifi_cfg.sta.ssid) - 1);
  strncpy((char*)wifi_cfg.sta.password, saved_config_.wifi_password, sizeof(wifi_cfg.sta.password) - 1);

  esp_wifi_disconnect();
  esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg);
  esp_wifi_connect();
}

void BalizamentoController::startAP() {
  // AP gerenciado pelo ESPHome via YAML (ap_timeout: 0s)
  ap_started_ = true;
  ESP_LOGI(TAG, "AP AeroControl ativo (gerenciado pelo ESPHome)");
}

// ==================== CALLBACKS DO YAML ====================
void balizamento_on_message(const std::string &payload, float energia) {
  if (g_controller) g_controller->handleBalCommand(payload, energia);
}

void sdm120_on_message(const std::string &payload) {
  if (!g_controller) return;
  g_controller->incrementMqttReceivedCount();
  ESP_LOGI(TAG, "MQTT RECEBIDO [%s]: %s", g_controller->getSdmWriteTopic().c_str(), payload.c_str());
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, payload) == DeserializationError::Ok) {
    const char *cmd = doc["comando"];
    if (cmd && strcmp(cmd, "ReadRegistersEnergy") == 0) {
      g_controller->publishEnergyRegisters();
    }
  }
}
