import serial
import threading
import time
import json
import os

# Configuración
SERIAL_PORT = "/dev/ttyACM0"  # Cambia a COM3 en Windows
BAUDRATE = 115200

# Archivos compartidos
STATE_FILE = "/tmp/motor_state.json"
CMD_FILE = "/tmp/motor_cmd.txt"

# Variable global para el estado
estado_actual = {
    "comando": "P",
    "estado": "PARADO",
    "pulsos": 0,
    "vueltas": 0.0,
    "rpm": 0.0
}

def guardar_estado():
    """Guarda el estado actual en archivo JSON"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(estado_actual, f)
    except Exception as e:
        print(f"Error guardando estado: {e}")

def leer_serial(ser):
    """Hilo que lee continuamente del serial"""
    global estado_actual
    
    while True:
        try:
            if ser.in_waiting:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if linea:
                    print(f"Serial: {linea}")
                
                # Formato esperado: COMANDO:A,ESTADO:ADELANTE,PULSOS:1234,VUELTAS:0.3856,RPM:1250.50
                if linea.startswith("COMANDO:") and ",ESTADO:" in linea:
                    partes = linea.split(",")
                    if len(partes) >= 5:
                        try:
                            estado_actual = {
                                "comando": partes[0].split(":")[1],
                                "estado": partes[1].split(":")[1],
                                "pulsos": int(partes[2].split(":")[1]),
                                "vueltas": float(partes[3].split(":")[1]),
                                "rpm": float(partes[4].split(":")[1])
                            }
                            guardar_estado()
                            print(f"✓ Estado actualizado - RPM: {estado_actual['rpm']:.2f}")
                        except (ValueError, IndexError) as e:
                            print(f"Error parseando: {e}")
                
                # Respuesta a comandos
                elif linea.startswith("OK:"):
                    print(f"Comando ejecutado: {linea}")
                    
        except Exception as e:
            print(f"Error en lectura serial: {e}")
            time.sleep(0.1)

def enviar_comandos(ser):
    """Hilo que lee comandos del archivo y los envía al Arduino"""
    ultimo_comando = ""
    
    while True:
        try:
            # Verificar si hay archivo de comando
            if os.path.exists(CMD_FILE):
                with open(CMD_FILE, 'r') as f:
                    comando = f.read().strip()
                
                # Si hay un comando nuevo
                if comando and comando != ultimo_comando:
                    print(f"Enviando comando: {comando}")
                    ser.write((comando + "\n").encode())
                    ultimo_comando = comando
                    
                    # Limpiar archivo después de leer
                    with open(CMD_FILE, 'w') as f:
                        f.write("")
                        
        except Exception as e:
            print(f"Error enviando comando: {e}")
        
        time.sleep(0.1)

def main():
    print("=== SERVIDOR TCP SIMPLIFICADO ===")
    print(f"Puerto serial: {SERIAL_PORT}")
    print(f"Baud rate: {BAUDRATE}")
    print(f"Archivo estado: {STATE_FILE}")
    print(f"Archivo comandos: {CMD_FILE}")
    print("==================================")
    
    try:
        # Conectar al Arduino
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
        print(f"✓ Conectado a Arduino en {SERIAL_PORT}")
        
        # Inicializar archivos
        guardar_estado()
        if not os.path.exists(CMD_FILE):
            with open(CMD_FILE, 'w') as f:
                f.write("")
        
        # Iniciar hilos
        hilo_lectura = threading.Thread(target=leer_serial, args=(ser,), daemon=True)
        hilo_lectura.start()
        
        hilo_comandos = threading.Thread(target=enviar_comandos, args=(ser,), daemon=True)
        hilo_comandos.start()
        
        print("✓ Servidor funcionando correctamente")
        print("Presiona Ctrl+C para detener\n")
        
        # Mantener el programa corriendo
        while True:
            time.sleep(1)
            
    except serial.SerialException as e:
        print(f"✗ Error abriendo puerto serial: {e}")
        print(f"Verifica que el Arduino esté conectado y el puerto sea correcto")
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
