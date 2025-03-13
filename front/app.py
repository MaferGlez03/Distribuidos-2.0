from flask import Flask, request, jsonify, render_template, send_from_directory, session
from flask_cors import CORS
import os
import hashlib
import socket
import ast

BROADCAST_IP = "255.255.255.255"
UDP_PORT = 8888

# Obtén el directorio de trabajo actual
basedir = os.getcwd()

app = Flask(__name__, 
            template_folder=os.path.join(basedir, 'frontend/templates'), 
            static_folder=os.path.join(basedir, 'backend/staticfiles')
            )
CORS(app)  # Esto permite que el frontend (posiblemente en otro dominio) pueda comunicarse

def find_active_server(start_ip, end_ip, port, timeout=1):
    """
    Escanea un rango de direcciones IP buscando un servidor que responda en el puerto especificado.
    """
    start_parts = list(map(int, start_ip.split('.')))
    end_parts = list(map(int, end_ip.split('.')))

    for last_octet in range(start_parts[3], end_parts[3] + 1):
        ip = f"{start_parts[0]}.{start_parts[1]}.{start_parts[2]}.{last_octet}"
        
        try:
            with socket.create_connection((ip, port), timeout=timeout) as s:
                print(f"✅ Servidor encontrado en {ip}:{port}")
                return ip  # Devuelve la primera IP que responda correctamente
        
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass  # Ignora los errores y pasa a la siguiente IP

    print("❌ No se encontró ningún servidor en el rango especificado.")
    return None  # No se encontró ningún servidor

def connect_to_server(server_ip, server_port, operation, data):
    """Conecta al servidor Chord por TCP y envía una solicitud."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((server_ip, int(server_port)))  # 🔹 Conectar al servidor TCP
            s.sendall(f'{operation}|{data}'.encode('utf-8'))
            return s.recv(10240).decode('utf-8').strip()
    except Exception as e:
        return f"Error en la conexión: {e}"

def generate_id_(ip):
    """Genera un ID único basado en el hash de la IP y puerto."""
    node_info = f"{ip}"
    return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)

def available_server():
    print("🔍 Buscando servidores activos...")
    server_ip = find_active_server("10.0.11.1", "10.0.11.20", 8000)

    if not server_ip:
        print("❌ No se encontraron servidores Chord. Intente nuevamente.")

    print("✅ Servidor(es) disponible(s):", server_ip)
    return server_ip

# Cargar la página principal sin hacer operaciones en la base de datos
@app.route("/")
def index():
    return render_template("index.html")

# Cargar la página principal sin hacer operaciones en la base de datos
@app.route("/register/")
def register():
    return render_template("register.html")

@app.route("/login/")
def login():
    return render_template("login.html")

@app.route("/forgot/")
def forgot():
    return render_template("forgot.html")

# Ruta para servir archivos estáticos (JS y CSS)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(app.static_folder), filename)


# ----------------------------
# Endpoints para Usuarios
# ----------------------------

#! Endpoint para registrar usuario
@app.route('/sign_up/', methods=['POST'])
def sign_up():
    data = request.get_json()
    name = data.get('username')
    email = data.get('email')
    password = data.get('password')
    chord_id = generate_id_(name)
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "reg", f"{chord_id}|{name}|{email}|{password}")
    app.logger.info(f"Respuesta del servidor: {response}")
    response2 = ast.literal_eval(response)
    app.logger.info(f"Respuesta del servidor: {response2}")
    if response != 'None':  # Suponiendo que el servidor devuelve "éxito" en caso de registro exitoso
        return jsonify({'message': f"🔹 Respuesta del servidor", 'user_id': response2[0], 'username': response2[1], 'chord_id': chord_id}), 201
    else:
        return jsonify({'message': 'Error al registrar el usuario'}), 400

#! Endpoint para iniciar sesión
@app.route('/log_in/', methods=['POST'])
def log_in():
    server_ip = available_server()
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    chord_id = generate_id_(username)

    # Crear el mensaje
    message = f"{chord_id}|{username}|{password}"
    print(f"Mensaje enviado: {message}")

    response = connect_to_server(server_ip, 8000, "log", f"{chord_id}|{username}|{password}")
    response2 = ast.literal_eval(response)
    if response:    # Suponiendo que el servidor devuelve "éxito" en caso de registro exitoso
        return jsonify({'message': f"🔹 Respuesta del servidor", 'user_id': response2[0], 'username': response2[1], 'chord_id': chord_id}), 201
    else:
        return jsonify({'message': 'Usuario no registrado'}), 401

# ----------------------------
# Endpoints para Contactos
# ----------------------------

#! Endpoint para agregar un contacto
@app.route('/contacts/', methods=['POST'])
def add_contact():
    server_ip = available_server()
    data = request.get_json()
    user_id = data.get('user_id')
    contact_name = data.get('contact_name')
    owner_id = data.get('owner_id')
    chord_id = data.get('chord_id')
    if user_id == owner_id:
        return jsonify({'message': 'Error, no se permite auto contacto'}), 400
    response = connect_to_server(server_ip, 8000, "add_contact", f"{chord_id}|{contact_name}|{owner_id}")
    bool_response = bool(response)
    if bool_response:
        return jsonify({'message': 'Contacto agregado'}), 201
    else:
        return jsonify({'message': 'Error al agregar el contacto'}), 400

#! Endpoint para listar contactos
@app.route('/contacts/<int:contact_id>/<int:chord_id>', methods=['GET'])
def list_contacts(contact_id, chord_id):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "list_contacts", f"{chord_id}|{contact_id}")
    app.logger.info(f"Respuesta del servidor: {response}")
    return jsonify(response), 200

#! Endopoint para eliminar contactos
@app.route('/contacts/<int:contact_id>/delete/<int:chord_id>', methods=['DELETE'])
def delete_contact(contact_id, chord_id):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "remove_contact", f"{chord_id}|{contact_id}")
    if response:
        return jsonify({'message': 'Contacto eliminado de la lista'}), 200
    else:
        return jsonify({'message': 'Error al eliminar contacto de la lista'}), 400

# ----------------------------
# Endpoints para Eventos
# ----------------------------

#! Endpoint para crear evento
@app.route('/create_event/', methods=['POST'])
def create_event():
    server_ip = available_server()
    data = request.get_json()
    event_name = data.get('title')
    event_date = data.get('start_time')  # Formato: 'YYYY-MM-DD'
    owner_id = data.get('owner_id')
    privacy = data.get('privacy')
    chord_id = data.get('chord_id')
    app.logger.info(f"Respuesta del servidor: {event_name}")
    app.logger.info(f"Respuesta del servidor: {event_date}")
    app.logger.info(f"Respuesta del servidor: {owner_id}")
    app.logger.info(f"Respuesta del servidor: {privacy}")
    app.logger.info(f"Respuesta del servidor: {chord_id}")
    response = connect_to_server(server_ip, 8000, "create_event", f"{chord_id}|{event_name}|{event_date}|{owner_id}|{privacy}")
    bool_response = bool(response)
    if bool_response:
        return jsonify({'message': 'Evento creado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al crear el evento'}), 400

#! Endpoint para crear evento grupal
@app.route('/create_group_event/', methods=['POST'])
def create_group_event():
    server_ip = available_server()
    data = request.get_json()
    event_name = data.get('title')
    event_date = data.get('start_time')  # Formato: 'YYYY-MM-DD'
    owner_id = data.get('owner_id')
    chord_id = data.get('chord_id')
    group_id = data.get('group_id')
    response = connect_to_server(server_ip, 8000, "create_group_event", f"{chord_id}|{event_name}|{event_date}|{owner_id}|{group_id}")
    bool_response = bool(response)
    if bool_response:
        return jsonify({'message': 'Evento grupal creado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al crear el evento grupal'}), 400

# # Endpoint para crear evento individual
# @app.route('/create_individual_event/', methods=['POST'])
# def create_individual_event():
#     server_ip = available_server()
#     data = request.get_json()
#     name = data.get('name')
#     date = data.get('date')
#     owner_id = data.get('owner_id')
#     contact_id = data.get('contact_id')
#     if server.create_individual_event(owner_id,name, date, contact_id)==f"Event created: {name}":
#         return jsonify({'message': 'Evento individual creado exitosamente'}), 201
#     else:
#         return jsonify({'message': 'Error al crear el evento individual'}), 400

#! Endpoint para confirmar evento
@app.route('/confirm_event/<int:event_id>/<int:chord_id>/<int:user_id>/', methods=['POST'])
def confirm_event(event_id, chord_id, user_id):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "confirm_event", f"{chord_id}|{user_id}|{event_id}")
    bool_response = bool(response)
    if bool_response:
        return jsonify({'message': 'Evento confirmado exitosamente'}), 200
    else:
        return jsonify({'message': 'Error al confirmar el evento'}), 400

#! Endpoint para listar eventos
@app.route('/list_events/<int:chord_id>/<string:user_name>/', methods=['GET'])
def list_events(chord_id, user_name):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "list_events", f"{chord_id}|{user_name}")
                
    return jsonify(response), 200

#! Endpoint para listar eventos pendientes
@app.route('/list_events_pending/<int:chord_id>/<string:username>/', methods=['GET'])
def list_events_pending(chord_id, username):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "list_events_pending", f"{chord_id}|{username}")
    return jsonify(response), 200

# ----------------------------
# Endpoints para Grupos
# ----------------------------

#! Endpoint para crear grupo
@app.route('/create_group/', methods=['POST'])
def create_group():
    server_ip = available_server()
    data = request.get_json()
    group_name = data.get('name')
    chord_id = data.get('chord_id')
    user_id = data.get('user_id')
    response = connect_to_server(server_ip, 8000, "create_group", f"{chord_id}|{group_name}|{user_id}")
    app.logger.info(f"Respuesta del servidor al crear grupo: {response}")
    if response:
        return jsonify({'message': 'Grupo creado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al crear el grupo'}), 400

#! Adicionar miembro a grupo
@app.route('/add_member_to_group/', methods=['POST'])
def add_member_to_group():
    server_ip = available_server()
    data = request.get_json()
    group_id = data.get('group_id')
    member_id = data.get('user_id')
    role = data.get('role', 'member')
    chord_id = data.get('chord_id')
    response = connect_to_server(server_ip, 8000, "add_member_to_group", f"{chord_id}|{group_id}|{member_id}|{role}")
    if response:
        return jsonify({'message': 'Miembro agregado al grupo'}), 201
    else:
        return jsonify({'message': 'Error al agregar miembro al grupo'}), 400

#! Eliminar miembro de un grupo
@app.route('/remove_member_from_group/<int:group_id>/<int:member_id>/<int:chord_id>/<string:username>/', methods=['DELETE'])
def remove_member_from_group(group_id, member_id, chord_id, username):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "remove_member_from_group", f"{chord_id}|{group_id}|{member_id}|{username}")
    if response:
        return jsonify({'message': response}), 201
    else:
        return jsonify({'message': 'Error al remover miembro del grupo'}), 400

#! Listar grupos
@app.route('/list_groups/<int:chord_id>/<string:username>/', methods=['GET'])
def list_groups(chord_id, username):
    app.logger.info(f"Username: {username}")
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "list_groups", f"{chord_id}|{username}")
    app.logger.info(f"Respuesta del servidor al listar grupos: {response}")
    return jsonify(response), 200

#! Listar miembros de un grupo
@app.route('/list_members/<int:group_id>/<int:chord_id>/', methods=['GET'])
def list_members(group_id, chord_id):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "list_member", f"{chord_id}|{group_id}")
    return jsonify(response), 200

#! Eliminar grupo
@app.route('/delete_group/<int:group_id>/<int:chord_id>/', methods=['DELETE'])
def delete_group(group_id, chord_id):
    server_ip = available_server()
    response = connect_to_server(server_ip, 8000, "delete_group", f"{chord_id}|{group_id}")
    if response:
        return jsonify({'message': 'Grupo eliminado'}), 200
    else:
        return jsonify({'message': 'Error al eliminar el grupo'}), 400

# ----------------------------
# Ejecutar la aplicación
# ----------------------------

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)


#! ########################################
#? Herencia en grupo
# Aceptar o declinar invitacion
# Mejorar apartado de user + campana
# Mejorar perfil (username y eliminar cosas)
#* Menu para eventos creados 
# Eliminar evento
# Editar evento
#* Agendas
# Agenda integrante grupo
# Agenda contacto
# Agenda grupo
# *
# Arreglar errores (alerts)
#! ########################################

