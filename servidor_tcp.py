import socket
import serial
import threading
import time

# --- CONFIGURACIÓN ---
SERIAL_PORT = "/dev/ttyACM0"   # Ajusta según tu sistema (ej. COM3 en Windows)
BAUDRATE = 115200
HOST = "0.0.0.0"
PORT = 5001
# ----------------------

# Variables globales para el estado
ultimo_comando = 'P'
ultimo_estado = "PARADO"
ultimos_pulsos = 0
ultimas_vueltas = 0.0
ultimas_rpm = 0.0
lock = threading.Lock()

def leer_serial(ser):
    """Hilo que lee continuamente del serial y actualiza los valores."""
    global ultimo_comando, ultimo_estado, ultimos_pulsos, ultimas_vueltas, ultimas_rpm
    
    while True:
        try:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if linea:
                print(f"Serial: {linea}")  # Debug
            
            # Formato esperado: "COMANDO:A,ESTADO:ADELANTE,PULSOS:1234,VUELTAS:0.3856,RPM:1250.50"
            if linea.startswith("COMANDO:") and ",ESTADO:" in linea:
                partes = linea.split(",")
                if len(partes) >= 5:
                    try:
                        with lock:
                            ultimo_comando = partes[0].split(":")[1]
                            ultimo_estado = partes[1].split(":")[1]
                            ultimos_pulsos = int(partes[2].split(":")[1])
                            ultimas_vueltas = float(partes[3].split(":")[1])
                            ultimas_rpm = float(partes[4].split(":")[1])
                        print(f"Actualizado - Estado: {ultimo_estado}, RPM: {ultimas_rpm:.2f}")
                    except (ValueError, IndexError) as e:
                        print(f"Error parseando datos: {e}")
                        
        except Exception as e:
            print(f"Error serial: {e}")
            time.sleep(0.1)

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.5)
        print(f"Conectado a Arduino en {SERIAL_PORT} a {BAUDRATE} baudios")
    except Exception as e:
        print(f"Error al abrir puerto serial: {e}")
        return

    # Iniciar hilo de lectura serial
    hilo_serial = threading.Thread(target=leer_serial, args=(ser,), daemon=True)
    hilo_serial.start()

    # Crear socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Servidor TCP escuchando en {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Conexión desde {addr}")
                data = conn.recv(1024)
                if not data:
                    continue

                cmd = data.decode("utf-8", errors="ignore").strip().upper()
                
                if cmd == "GET_STATE":
                    with lock:
                        respuesta = f"COMANDO:{ultimo_comando},ESTADO:{ultimo_estado},PULSOS:{ultimos_pulsos},VUELTAS:{ultimas_vueltas:.4f},RPM:{ultimas_rpm:.2f}"
                    conn.sendall((respuesta + "\n").encode("utf-8"))
                
                elif cmd in ["A", "R", "P", "Z"]:
                    # Enviar comando al Arduino
                    ser.write((cmd + "\n").encode())
                    conn.sendall(b"OK\n")
                    print(f"Comando enviado: {cmd}")
                
                else:
                    conn.sendall(b"ERR:CMD\n")

if __name__ == "__main__":
    main()
