from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
import json
import os

# Configuración
APP_USER = "admin"
# Genera tu hash con: from werkzeug.security import generate_password_hash; print(generate_password_hash("tu_password"))
APP_PW_HASH = "scrypt:32768:8:1$K2xRt8vNlZqW9YpX$8d9f2a1b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d"
SECRET_KEY = "clave-secreta-para-sesiones-cambiar-en-produccion"

# Archivo compartido con el estado del motor
STATE_FILE = "/tmp/motor_state.json"
CMD_FILE = "/tmp/motor_cmd.txt"

app = Flask(__name__)
app.secret_key = SECRET_KEY

def is_logged_in():
    return session.get("logged_in") is True

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
    """Devuelve el estado actual del motor desde el archivo compartido"""
    if not is_logged_in():
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                estado = json.load(f)
            return jsonify({"ok": True, **estado})
        else:
            return jsonify({"ok": False, "error": "No hay datos del motor"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.post("/api/comando")
def enviar_comando():
    """Envía un comando al motor escribiendo en el archivo compartido"""
    if not is_logged_in():
        return jsonify({"ok": False, "error": "No autorizado"}), 401
    
    data = request.get_json()
    cmd = data.get("comando", "").upper()
    
    if cmd not in ["A", "R", "P", "Z"]:
        return jsonify({"ok": False, "error": "Comando inválido"})
    
    try:
        # Escribir comando en archivo para que lo lea el servidor TCP
        with open(CMD_FILE, 'w') as f:
            f.write(cmd)
        return jsonify({"ok": True, "mensaje": f"Comando {cmd} enviado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

if __name__ == "__main__":
    print("=== APLICACIÓN WEB ===")
    print("Servidor Flask iniciando...")
    print("Accede a: http://localhost:5000")
    print("======================")
    app.run(host="0.0.0.0", port=5000, debug=True)
