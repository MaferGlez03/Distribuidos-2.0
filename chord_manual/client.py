import hashlib
import socket
import random

BROADCAST_IP = "255.255.255.255"
UDP_PORT = 8888

def discover_servers():
    """Envía un broadcast UDP y recibe respuestas de servidores activos."""
    servers = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2)

        s.sendto(b"DISCOVER", (BROADCAST_IP, UDP_PORT))

        try:
            while True:
                data, addr = s.recvfrom(1024)
                servers.append(data.decode())
        except socket.timeout:
            pass  

    return servers

def connect_to_server(server_ip, server_port, operation, data):
    """Conecta al servidor Chord por TCP y envía una solicitud."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, int(server_port)))  # 🔹 Conectar al servidor TCP
            # 🔹 Enviar mensaje correctamente
            s.sendall(f'{operation}|{data}'.encode('utf-8'))
            # print(f"Mensaje enviado correctamente vía TCP. Operation: {op} Data: {data}")
            return s.recv(1024)
    except Exception as e:
        return f"Error en la conexión: {e}"
def generate_id_( ip):
        """Genera un ID único basado en el hash de la IP y puerto."""
        # Obtener mi IP
        node_info = f"{ip}"
        return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)

if __name__ == "__main__":
    print("Cliente Chord iniciado.")
    while True:
        print("🔹 Cliente Chord iniciado.")

 
        print("\n🔹 Menú de Opciones:")
        print("1. Registrar usuario")
        print("2. Salir")

        opcion = input("Seleccione una opción: ")

        # Buscar servidores antes de cada operación
        print("🔍 Buscando servidores activos...")
        servers = discover_servers()

        if not servers:
            print("❌ No se encontraron servidores Chord. Intente nuevamente.")
            continue  # Volver al menú

        print("✅ Servidores disponibles:", servers)

        selected_server = random.choice(servers)  # Seleccionar un servidor
        server_ip, server_port = selected_server.split(":")

        if opcion == "1":
            print("\n🔹 Registro de Usuario:")
            name = input("Ingrese su nombre: ")
            email = input("Ingrese su correo electrónico: ")
            password = input("Ingrese su contraseña: ")
            user_id = generate_id_(name)
            print(f"user_id: { user_id}")
            # Enviar la solicitud al servidor
            response = connect_to_server(server_ip, server_port, "reg", f"{user_id}|{name}|{email}|{password}").decode()
            print(f"🔹 Respuesta del servidor: {response}")
        elif opcion == "2":
            response = connect_to_server(server_ip, server_port, "create_event", "456|Evento1|2024-12-01")
        elif opcion == "3":
            response = connect_to_server(server_ip, server_port, "list_events", "123")
        elif opcion == "4":
            break
        print(f"Respuesta del servidor: {response}")