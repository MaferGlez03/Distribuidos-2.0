# def connect_to_server(server_ip, server_port, operation, data):
#     """Conecta al servidor Chord con SSL y envía una solicitud."""
#     try:
#         context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
#         context.check_hostname = False
#         context.verify_mode = ssl.CERT_NONE
#         # context.load_verify_locations("ssl/certificate.pem")  # Cargar certificado

#         with socket.create_connection((server_ip, server_port)) as sock:
#             with context.wrap_socket(sock, server_hostname="MFSG") as secure_sock:
#                 secure_sock.sendall(f'{operation}|{data}'.encode('utf-8'))
#                 return secure_sock.recv(1024).decode()
#     except Exception as e:
#         return f"Error en la conexión SSL: {e}"
import hashlib
import socket
import random
import ssl

BROADCAST_IP = "255.255.255.255"
UDP_PORT = 8888

# Variable global para almacenar el ID del usuario registrado
chord_id = None
username=None

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
            return s.recv(1024).decode('utf-8').strip()
    except Exception as e:
        return f"Error en la conexión: {e}"

def generate_id_(ip):
    """Genera un ID único basado en el hash de la IP y puerto."""
    node_info = f"{ip}"
    return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)

def select_in(option: str) -> str:
    if option == 'privacy':
        while True:
            option = input("Ingrese la privacidad del evento ('public' o 'private'): ").strip().lower()
            if option in ['private', 'public']:
                return option
            else:
                print("Opción no válida. Por favor, elige 'public' o 'private'.")
    if option == '':
        while True:
            option = input("").strip().upper()
            if option in []:
                return option
            else:
                print("Opción no válida. Por favor, elige ")


def unregister_user():
    """
    Desregistra al usuario actual, vaciando la variable chord_id.
    """
    global chord_id
    if chord_id is not None:
        print(f"🔹 Usuario con ID {chord_id} desregistrado.")
        chord_id = None
        username=None
    else:
        print("🔹 No hay ningún usuario registrado.")

if __name__ == "__main__":
    print("🔹 Cliente Chord iniciado.")
    while True:
        print("\n🔹 Menú de Opciones:")
        print("1. Registrar usuario")
        print("2. Desregistrar usuario")
        print("3. Crear evento")
        print("4. Listar eventos")
        print("5. Confirmar evento")
        print("6. Cancelar evento")
        print("7. Listar eventos pendientes")
        print("8. Añadir contacto")
        print("9. Eliminar contacto")
        print("10. Listar contactos")
        print("11. Crear grupo")
        print("12. Eliminar grupo")
        print("13. Abandonar grupo")
        print("14. Añadir miembro a grupo")
        print("15. Eliminar miembro de grupo")
        print("16. Listar grupos")
        print("17. Listar miembros de grupo")
        print("18. Listar agenda personal")
        print("19. Listar agenda de grupo")
        print("20. Salir")

        opcion = input("Seleccione una opción: ")

        if opcion == "20":
            print("Saliendo del cliente Chord...")
            break

        # Buscar servidores antes de cada operación
        print("🔍 Buscando servidores activos...")
        server_ip = find_active_server("10.0.11.1", "10.0.11.20", 8000)

        if not server_ip:
            print("❌ No se encontraron servidores Chord. Intente nuevamente.")
            continue  # Volver al menú

        print("✅ Servidor(es) disponible(s):", server_ip)

        if opcion == "1":
            print("\n🔹 Registro de Usuario:")
            name = input("Ingrese su nombre: ")
            email = input("Ingrese su correo electrónico: ")
            password = input("Ingrese su contraseña: ")
            user_id = generate_id_(name)
            print(f"user_id: {user_id}")
            response = connect_to_server(server_ip, 8000, "reg", f"{user_id}|{name}|{email}|{password}")
            if "registered" in response.lower():  # Suponiendo que el servidor devuelve "éxito" en caso de registro exitoso
                chord_id = user_id  # Actualizar chord_id con el ID del usuario registrado
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "2":
            print("\n🔹 Desregistrar Usuario:")
            unregister_user()

        elif opcion in ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]:
            if chord_id is None:
                print("❌ Debe registrarse primero para realizar esta operación.")
                continue

            if opcion == "3":
                print("\n🔹 Crear Evento:")
                event_name = input("Ingrese el nombre del evento: ")
                event_date = input("Ingrese la fecha del evento (YYYY-MM-DD): ")
                owner = input("Ingrese su nombre: ")
                privacy = "private"
                response = connect_to_server(server_ip, 8000, "create_event", f"{chord_id}|{event_name}|{event_date}|{owner}|{privacy}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "4":
                print("\n🔹 Listar Eventos:")
                user = input("Ingrese su nombre: ")
                response = connect_to_server(server_ip, 8000, "list_events", f"{chord_id}|{user}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "5":
                print("\n🔹 Confirmar Evento:")
                event_id = input("Ingrese el ID del evento: ")
                response = connect_to_server(server_ip, 8000, "confirm_event", f"{chord_id}|{event_id}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "6":
                print("\n🔹 Cancelar Evento:")
                event_id = input("Ingrese el ID del evento: ")
                response = connect_to_server(server_ip, 8000, "cancel_event", f"{chord_id}|{event_id}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "7":
                print("\n🔹 Listar Eventos Pendientes:")
                response = connect_to_server(server_ip, 8000, "list_events_pending", chord_id)
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "8":
                print("\n🔹 Añadir Contacto:")
                contact_name = input("Ingrese el nombre del contacto: ")
                user_id = input("Ingrese el ID del contacto: ")
                response = connect_to_server(server_ip, 8000, "add_contact", f"{chord_id}|{user_id}|{contact_name}|{username}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "9":
                print("\n🔹 Eliminar Contacto:")
                contact_id = input("Ingrese el ID del contacto: ")
                response = connect_to_server(server_ip, 8000, "remove_contact", f"{chord_id}|{contact_id}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "10":
                print("\n🔹 Listar Contactos:")
                response = connect_to_server(server_ip, 8000, "list_contacts", f"{chord_id}|{username}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "11":
                print("\n🔹 Crear Grupo:")
                group_name = input("Ingrese el nombre del grupo: ")
                response = connect_to_server(server_ip, 8000, "create_group", f"{chord_id}|{group_name}|{username}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "12":
                print("\n🔹 Eliminar Grupo:")
                group_id = input("Ingrese el id del grupo: ")
                response = connect_to_server(server_ip, 8000, "delete_group", f"{chord_id}|{group_id}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "13":
                print("\n🔹 Abandonar Grupo:")
                group_name = input("Ingrese el nombre del grupo: ")
                response = connect_to_server(server_ip, 8000, "leave_group", f"{chord_id}|{group_name}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "14":
                print("\n🔹 Añadir Miembro a Grupo:")
                group_id = input("Ingrese el ID del grupo: ")
                member_id = input("Ingrese el ID del miembro a añadir: ")
                role = input("Ingrese el rol del miembro: ")
                response = connect_to_server(server_ip, 8000, "add_member_to_group", f"{chord_id}|{group_id}|{member_id}|{role}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "15":
                print("\n🔹 Eliminar Miembro de Grupo:")
                group_id = input("Ingrese el ID del grupo: ")
                member_id = input("Ingrese el ID del miembro a eliminar: ")
                response = connect_to_server(server_ip, 8000, "remove_member_from_group", f"{chord_id}|{group_id}|{member_id}|{username}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "16":
                print("\n🔹 Listar Grupos:")
                response = connect_to_server(server_ip, 8000, "list_group", f"{chord_id}|{username}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "17":
                print("\n🔹 Listar Miembros de Grupo:")
                group_id = input("Ingrese el ID del grupo: ")
                response = connect_to_server(server_ip, 8000, "list_member", f"{chord_id}|{group_id}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "18":
                print("\n🔹 Listar Agenda Personal:")
                response = connect_to_server(server_ip, 8000, "list_personal_agenda", f"{chord_id}|{username}")
                print(f"🔹 Respuesta del servidor: {response}")

            elif opcion == "19":
                print("\n🔹 Listar Agenda de Grupo:")
                group_id = input("Ingrese el ID del grupo: ")
                response = connect_to_server(server_ip, 8000, "list_group_agenda", f"{chord_id}|{group_id}|{username}")
                print(f"🔹 Respuesta del servidor: {response}")

        else:
            print("❌ Opción no válida. Intente nuevamente.")