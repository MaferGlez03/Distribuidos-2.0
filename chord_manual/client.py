import hashlib
import socket
import random
import ssl

BROADCAST_IP = "255.255.255.255"
UDP_PORT = 8888

def find_active_server(start_ip, end_ip, port, timeout=1):
    """
    Escanea un rango de direcciones IP buscando un servidor que responda en el puerto especificado.

    :param start_ip: IP inicial del rango (ej. "10.0.11.1")
    :param end_ip: IP final del rango (ej. "10.0.11.20")
    :param port: Puerto a probar en cada IP (ej. 8003)
    :param timeout: Tiempo máximo de espera por cada conexión (en segundos)
    :return: La IP del servidor encontrado o None si no se encontró ninguno
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
    """Conecta al servidor Chord con SSL y envía una solicitud."""
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # context.load_verify_locations("ssl/certificate.pem")  # Cargar certificado

        with socket.create_connection((server_ip, int(8000))) as sock:
            with context.wrap_socket(sock, server_hostname=server_ip) as secure_sock:
                secure_sock.sendall(f'{operation}|{data}'.encode('utf-8'))
                return secure_sock.recv(1024).decode()
    except Exception as e:
        return f"Error en la conexión SSL: {e}"

def generate_id_(ip):
    """Genera un ID único basado en el hash de la IP y puerto."""
    node_info = f"{ip}"
    return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)

if __name__ == "__main__":
    print("🔹 Cliente Chord iniciado.")
    while True:
        print("\n🔹 Menú de Opciones:")
        print("1. Registrar usuario")
        print("2. Crear evento")
        print("3. Listar eventos")
        print("4. Confirmar evento")
        print("5. Cancelar evento")
        print("6. Listar eventos pendientes")
        print("7. Añadir contacto")
        print("8. Eliminar contacto")
        print("9. Listar contactos")
        print("10. Crear grupo")
        print("11. Eliminar grupo")
        print("12. Abandonar grupo")
        print("13. Añadir miembro a grupo")
        print("14. Eliminar miembro de grupo")
        print("15. Listar grupos")
        print("16. Listar miembros de grupo")
        print("17. Listar agenda personal")
        print("18. Listar agenda de grupo")
        print("19. Salir")

        opcion = input("Seleccione una opción: ")

        # Buscar servidores antes de cada operación
        print("🔍 Buscando servidores activos...")
        server_ip = find_active_server("10.0.11.1", "10.0.11.20", 8000)

        if not server_ip:
            print("❌ No se encontraron servidores Chord. Intente nuevamente.")
            continue  # Volver al menú

        print("✅ Servidor disponibles:", server_ip)

        
        

        if opcion == "1":
            print("\n🔹 Registro de Usuario:")
            name = input("Ingrese su nombre: ")
            email = input("Ingrese su correo electrónico: ")
            password = input("Ingrese su contraseña: ")
            user_id = generate_id_(name)
            print(f"user_id: {user_id}")
            response = connect_to_server(server_ip,8000, "reg", f"{user_id}|{name}|{email}|{password}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "2":
            print("\n🔹 Crear Evento:")
            user_id = input("Ingrese su ID de usuario: ")
            event_name = input("Ingrese el nombre del evento: ")
            event_date = input("Ingrese la fecha del evento (YYYY-MM-DD): ")
            response = connect_to_server(server_ip, 8000, "create_event", f"{user_id}|{event_name}|{event_date}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "3":
            print("\n🔹 Listar Eventos:")
            user_id = input("Ingrese su ID de usuario: ")
            response = connect_to_server(server_ip, 8000, "list_events", user_id)
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "4":
            print("\n🔹 Confirmar Evento:")
            user_id = input("Ingrese su ID de usuario: ")
            event_id = input("Ingrese el ID del evento: ")
            response = connect_to_server(server_ip, 8000, "confirm_event", f"{user_id}|{event_id}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "5":
            print("\n🔹 Cancelar Evento:")
            user_id = input("Ingrese su ID de usuario: ")
            event_id = input("Ingrese el ID del evento: ")
            response = connect_to_server(server_ip, 8000, "cancel_event", f"{user_id}|{event_id}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "6":
            print("\n🔹 Listar Eventos Pendientes:")
            user_id = input("Ingrese su ID de usuario: ")
            response = connect_to_server(server_ip, 8000, "list_events_pending", user_id)
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "7":
            print("\n🔹 Añadir Contacto:")
            user_id = input("Ingrese su ID de usuario: ")
            contact_name = input("Ingrese el nombre del contacto: ")
            owner_id = input("Ingrese el ID del propietario: ")
            response = connect_to_server(server_ip, 8000, "add_contact", f"{user_id}|{contact_name}|{owner_id}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "8":
            print("\n🔹 Eliminar Contacto:")
            user_id = input("Ingrese su ID de usuario: ")
            contact_id = input("Ingrese el ID del contacto: ")
            response = connect_to_server(server_ip, 8000, "remove_contact", f"{user_id}|{contact_id}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "9":
            print("\n🔹 Listar Contactos:")
            user_id = input("Ingrese su ID de usuario: ")
            response = connect_to_server(server_ip, 8000, "list_contacts", user_id)
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "10":
            print("\n🔹 Crear Grupo:")
            owner_id = input("Ingrese su ID de usuario: ")
            group_name = input("Ingrese el nombre del grupo: ")
            response = connect_to_server(server_ip, 8000, "create_group", f"{owner_id}|{group_name}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "11":
            print("\n🔹 Eliminar Grupo:")
            owner_id = input("Ingrese su ID de usuario: ")
            group_name = input("Ingrese el nombre del grupo: ")
            response = connect_to_server(server_ip, 8000, "delete_group", f"{owner_id}|{group_name}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "12":
            print("\n🔹 Abandonar Grupo:")
            owner_id = input("Ingrese su ID de usuario: ")
            group_name = input("Ingrese el nombre del grupo: ")
            response = connect_to_server(server_ip, 8000, "leave_group", f"{owner_id}|{group_name}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "13":
            print("\n🔹 Añadir Miembro a Grupo:")
            user_id = input("Ingrese su ID de usuario: ")
            group_id = input("Ingrese el ID del grupo: ")
            member_id = input("Ingrese el ID del miembro a añadir: ")
            role = input("Ingrese el rol del miembro: ")
            response = connect_to_server(server_ip, 8000, "add_member_to_group", f"{user_id}|{group_id}|{member_id}|{role}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "14":
            print("\n🔹 Eliminar Miembro de Grupo:")
            user_id = input("Ingrese su ID de usuario: ")
            group_id = input("Ingrese el ID del grupo: ")
            member_id = input("Ingrese el ID del miembro a eliminar: ")
            response = connect_to_server(server_ip, 8000, "remove_member_from_group", f"{user_id}|{group_id}|{member_id}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "15":
            print("\n🔹 Listar Grupos:")
            user_id = input("Ingrese su ID de usuario: ")
            response = connect_to_server(server_ip, 8000, "list_group", user_id)
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "16":
            print("\n🔹 Listar Miembros de Grupo:")
            user_id = input("Ingrese su ID de usuario: ")
            group_id = input("Ingrese el ID del grupo: ")
            response = connect_to_server(server_ip, 8000, "list_member", f"{user_id}|{group_id}")
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "17":
            print("\n🔹 Listar Agenda Personal:")
            user_id = input("Ingrese su ID de usuario: ")
            response = connect_to_server(server_ip, 8000, "list_personal_agenda", user_id)
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "18":
            print("\n🔹 Listar Agenda de Grupo:")
            group_id = input("Ingrese el ID del grupo: ")
            response = connect_to_server(server_ip, 8000, "list_group_agenda", group_id)
            print(f"🔹 Respuesta del servidor: {response}")

        elif opcion == "19":
            print("Saliendo del cliente Chord...")
            break

        else:
            print("❌ Opción no válida. Intente nuevamente.")