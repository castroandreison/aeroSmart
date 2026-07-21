import serial
import serial.tools.list_ports
import time
import sys
from datetime import datetime

def listar_portas():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("Nenhuma porta serial encontrada.")
        sys.exit(1)
    print("Portas seriais disponiveis:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    return ports

def escolher_porta(ports):
    while True:
        try:
            idx = int(input("\nEscolha o numero da porta: "))
            if 0 <= idx < len(ports):
                return ports[idx].device
        except ValueError:
            pass
        print("Opcao invalida.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Monitor serial do ESP32")
    parser.add_argument("-p", "--port", help="Porta serial (ex: COM3)")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("-o", "--output", help="Salvar log em arquivo")
    args = parser.parse_args()

    port = args.port
    if not port:
        ports = listar_portas()
        port = escolher_porta(ports)

    baud = args.baud
    log_file = None
    if args.output:
        log_file = open(args.output, "w", encoding="utf-8")

    print(f"\nConectando a {port} a {baud} baud...")
    print("Pressione Ctrl+C para sair.\n")

    try:
        ser = serial.Serial(port, baud, timeout=1)
    except serial.SerialException as e:
        print(f"Erro ao abrir {port}: {e}")
        sys.exit(1)

    try:
        while True:
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{ts}] {line}")
                    if log_file:
                        log_file.write(f"[{ts}] {line}\n")
                        log_file.flush()
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuario.")
    finally:
        ser.close()
        if log_file:
            log_file.close()

if __name__ == "__main__":
    main()
