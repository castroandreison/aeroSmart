import paho.mqtt.client as mqtt
import json
import time
import sys

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_BAL_WRITE = "Bal/Write/AeroClub Adm"
TOPIC_BAL_READ = "Bal/Read/AeroClub Adm"
TOPIC_SDM_WRITE = "SDM120/Write/AeroClub Adm"
TOPIC_SDM_READ = "SDM120/Read/AeroClub Adm"
TOPIC_HEARTBEAT = "Heartbeat/AeroClub Adm"
#FIRMWARE_URL = "https://gitlab.com/castroandreison/aerocontrol/-/raw/main/latest.ota.bin"
FIRMWARE_URL = "https://github.com/castroandreison/aeroSmart/raw/refs/heads/main/Esta%C3%A7%C3%A3o%20de%20controle/esp32_balizamento/firmware.ota.bin"

def on_connect(client, userdata, flags, rc, *extra):
    if rc == 0:
        print(f"Conectado ao broker {BROKER}:{PORT}")
        client.subscribe(TOPIC_BAL_READ)
        client.subscribe(TOPIC_SDM_READ)
        client.subscribe(TOPIC_HEARTBEAT)
    else:
        print(f"Falha na conexao: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        print(f"[RECEBIDO] {msg.topic}: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"[RECEBIDO] {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Conectando ao broker {BROKER}:{PORT}...")
client.connect(BROKER, PORT, 60)
client.loop_start()
time.sleep(1)

def send(topic, payload):
    data = json.dumps(payload, ensure_ascii=False)
    print(f"[ENVIADO] {topic}: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    client.publish(topic, data)
    time.sleep(0.5)

def menu():
    print("\n" + "="*60)
    print("  SIMULADOR MQTT - AeroControl Balizamento")
    print("="*60)
    print(f"  Broker: {BROKER}:{PORT}")
    print(f"  Firmware: {FIRMWARE_URL}")
    print("="*60)
    print("  1 - BalOn (Ligar balizamento)")
    print("  2 - BalOff (Desligar balizamento)")
    print("  3 - BalOn com agendamento (X minutos)")
    print("  4 - UpdateFirmware (OTA via GitLab)")
    print("  5 - ReadRegistersEnergy (ler SDM120)")
    print("  6 - Solicitar Heartbeat")
    print("  0 - Sair")
    print("-"*60)

try:
    while True:
        menu()
        op = input("Opcao: ").strip()

        if op == "1":
            send(TOPIC_BAL_WRITE, {"comando": "BalOn"})

        elif op == "2":
            send(TOPIC_BAL_WRITE, {"comando": "BalOff"})

        elif op == "3":
            try:
                minutos = float(input("Minutos: ").strip())
            except:
                minutos = 5
            send(TOPIC_BAL_WRITE, {
                "comando": "BalOn",
                "agendamento": {"duracao_minutos": minutos}
            })

        elif op == "4":
            send(TOPIC_BAL_WRITE, {
                "comando": "UpdateFirmware",
                "url": FIRMWARE_URL
            })
            print("  -> OTA iniciado! Dispositivo vai reiniciar em alguns segundos.")

        elif op == "5":
            send(TOPIC_SDM_WRITE, {"comando": "ReadRegistersEnergy"})

        elif op == "6":
            send(TOPIC_BAL_WRITE, {"comando": "RequestHeartbeat"})
            print("  -> Heartbeat solicitado. Aguardando resposta...")

        elif op == "0":
            break

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nEncerrando...")
finally:
    client.loop_stop()
    client.disconnect()
    print("Desconectado.")
