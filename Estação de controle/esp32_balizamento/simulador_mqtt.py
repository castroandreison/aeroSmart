import paho.mqtt.client as mqtt
import json
import time
import sys

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_BAL_WRITE = "Bal/Write/AeroClub Central"
TOPIC_BAL_READ = "Bal/Read/AeroClub Central"
TOPIC_SDM_WRITE = "SDM120/Write/AeroClub Central"
TOPIC_SDM_READ = "SDM120/Read/AeroClub Central"
FIRMWARE_URL = "https://gitlab.com/castroandreison/aerocontrol/-/raw/main/latest.ota.bin"

def on_connect(client, userdata, flags, rc, *extra):
    if rc == 0:
        print(f"Conectado ao broker {BROKER}:{PORT}")
        client.subscribe(TOPIC_BAL_READ)
        client.subscribe(TOPIC_SDM_READ)
    else:
        print(f"Falha na conexao: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        print(f"[RECEBIDO] {msg.topic}: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"[RECEBIDO] {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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
    print("  6 - Enviar JSON personalizado")
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
            topic = input("Topico: ").strip()
            payload_raw = input("JSON: ").strip()
            try:
                payload = json.loads(payload_raw)
                send(topic, payload)
            except:
                print("JSON invalido")

        elif op == "0":
            break

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nEncerrando...")
finally:
    client.loop_stop()
    client.disconnect()
    print("Desconectado.")
