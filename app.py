from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import socket
import json

# --- CONFIGURACIÓN DE AUTENTICACIÓN ---
# Para generar un hash de tu contraseña, usa en Python:
# from werkzeug.security import generate_password_hash
# print(generate_password_hash("tu_contraseña"))
APP_USER = "admin"
APP_PW_HASH = "scrypt:32768:8:1$8xVnLZqW9YpK2xRt$8d9f2a1b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d"  # Reemplazar con hash real
SECRET_KEY = "clave-secreta-muy-larga-y-aleatoria-para-sesiones"
# ------------------------------------

TCP_HOST = "127.0.0.1"
TCP_PORT = 5001

app = Flask(__name__)
app.secret_key = SECRET_KEY

def is_logged_in():
    return session.get("logged_in") is True

def send_cmd(cmd: str) -> str:
    """Envía un comando TCP y devuelve la respuesta."""
    try:
        with socket.create_connection((TCP_HOST, TCP_PORT), timeout=2) as s:
            s.sendall((cmd + "\n").encode("utf-8"))
            return s.recv(1024).decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return f"ERR:{str(e)}"

def send_control_cmd(cmd: str) -> bool:
    """Envía un comando de control al Arduino (A, R, P, Z)."""
    try:
        with socket.create_connection((TCP_HOST, TCP_PORT), timeout=2) as s:
            s.sendall((cmd + "\n").encode("utf-8"))
            response = s.recv(1024).decode("utf-8", errors="ignore").strip()
            return response.startswith("OK")
    except Exception as e:
        print(f"Error enviando comando {cmd}: {e}")
        return False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pw = request.form.get("password", "")
        if user == APP_USER and check_password_hash(APP_PW_HASH, pw):
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Usuario o contraseña incorrectos")
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("index.html")

@app.get("/api/estado")
def get_estado():
    """Devuelve el estado actual del motor."""
    if not is_logged_in():
        return jsonify({"ok": False, "error": "No autorizado"}), 401

    resp = send_cmd("GET_STATE")
    # Se espera "COMANDO:A,ESTADO:ADELANTE,PULSOS:1234,VUELTAS:0.3856,RPM:1250.50"
    try:
        partes = resp.split(",")
        comando = partes[0].split(":")[1]
        estado = partes[1].split(":")[1]
        pulsos = int(partes[2].split(":")[1])
        vueltas = float(partes[3].split(":")[1])
        rpm = float(partes[4].split(":")[1])
        
        return jsonify({
            "ok": True,
            "comando": comando,
            "estado": estado,
            "pulsos": pulsos,
            "vueltas": vueltas,
            "rpm": rpm
        })
    except Exception as e:
        return jsonify({"ok": False, "error": f"Respuesta inválida: {resp}"})

@app.post("/api/comando")
def enviar_comando():
    """Envía un comando al motor (A=Adelante, R=Atrás, P=Paro, Z=Reset)."""
    if not is_logged_in():
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    data = request.get_json()
    cmd = data.get("comando", "").upper()
    
    if cmd not in ["A", "R", "P", "Z"]:
        return jsonify({"ok": False, "error": "Comando inválido"})
    
    if send_control_cmd(cmd):
        return jsonify({"ok": True, "mensaje": f"Comando {cmd} enviado"})
    else:
        return jsonify({"ok": False, "error": "Error al enviar comando"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
