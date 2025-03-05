import time
import os
import argparse
import docker
import subprocess
import shutil

from docker.errors import ImageNotFound, BuildError, APIError

# Configura el cliente de Docker
client = docker.from_env()

# Nombre de la red y el contenedor
NETWORK_NAME = 'chord-network'
IMAGE_NAME = 'agenda-image'
CONTAINER_PREFIX = 'agenda-server-'
ENV_FILE = '.env'

# Ruta del volumen compartido (en el host y en el contenedor)
# VOLUME_HOST_PATH = 'D:\\Distribuidos-2.0\\chord_manual\\first'
# VOLUME_CONTAINER_PATH = '\\shared'
VOLUME_HOST_PATH = '/media/daniman/Dani/UNI/4toano/Distribuidos/Proyecto/FinalTotal/Distribuidos-2.0/chord_manual/first'
VOLUME_CONTAINER_PATH = '/shared'  

def read_env(file_path=ENV_FILE):
    """Lee el archivo .env y devuelve los valores de PORT y CONTAINER_INDEX"""
    index = 0
    port = 3000
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            if line.startswith("PORT="):
                port = int(line.strip().split("=")[1])
            elif line.startswith("CONTAINER_INDEX="):
                index = int(line.strip().split("=")[1])
                
        if port is None and index is None:
            raise ValueError("PORT and INDEX not found in the .env file")
    return port, index

def update_env(file_path=ENV_FILE):
    """Lee y actualiza el archivo .env"""
    port, index = read_env(file_path)

    with open(file_path, "w") as file:
        file.write(f"PORT={port+1}\n")
        file.write(f"CONTAINER_INDEX={index+1}\n")

    return port+1, index+1

def create_network_if_not_exists():
    """Crea la red Docker si no existe"""
    networks = client.networks.list(names=[NETWORK_NAME])
    if not networks:
        print(f"Creating network: {NETWORK_NAME}")
        client.networks.create(NETWORK_NAME, driver='bridge')
    else:
        print(f"Network {NETWORK_NAME} already exists")



def manage_containers(action, container_name=None, container_index=None, container_ip=None):
    """Detiene y elimina contenedores según el prefijo, índice o IP dados, si se requiere"""
    filters = {"name": CONTAINER_PREFIX}
    containers = client.containers.list(all=True, filters=filters)

    # Depuración: Listar contenedores encontrados con sus IPs
    print(f"Containers found for action '{action}':")
    for container in containers:
        networks = container.attrs['NetworkSettings']['Networks']
        ip = 'No IP'
        for network in networks.values():
            ip = network.get('IPAddress', 'No IP')  # Usar 'IPAddress' para obtener la IP
            if ip != 'No IP':
                break
        print(f"Name: {container.name}, IP: {ip}")

    if container_ip:
        containers = [container for container in containers 
                      if any(network.get('IPAddress') == container_ip for network in container.attrs['NetworkSettings']['Networks'].values())]

    if container_index is not None:
        container_name = f"{CONTAINER_PREFIX}{container_index}"
        containers = [container for container in containers if container.name == container_name]

    if container_name:
        containers = [container for container in containers if container.name == container_name]

    if not containers:
        print(f"No containers found for action '{action}' with the provided filters.")
        return

    for container in containers:
        print(f"{action.capitalize()} container: {container.name}")
        
        if action == 'stop':
            container.stop()
        elif action == 'remove':
            if container.status == 'running':
                container.stop()
            container.remove()

def run_container_by_index(index):
    """Inicia un contenedor Docker dado un índice si ya existe."""
    container_name = f"{CONTAINER_PREFIX}{index}"
    
    # Verifica si el contenedor ya existe
    existing_containers = client.containers.list(all=True, filters={"name": container_name})
    
    if existing_containers:
        container = existing_containers[0]
        if container.status == 'running':
            print(f"Container {container_name} is already running.")
        else:
            print(f"Starting existing container: {container_name}")
            container.start()
        return container_name
    else:
        print(f"No existing container found with name {container_name}.")
        return None


def manage_image(action: str) -> None:
    """Elimina o construye la imagen Docker."""
    if action == 'remove':
        try:
            images = client.images.list(name=IMAGE_NAME)
            if not images:
                print(f"No image found with name {IMAGE_NAME}.")
                return
            
            for image in images:
                if image.tags:
                    print(f"Removing image: {image.tags[0]}")
                else:
                    print(f"Removing image with ID: {image.id}")
                
                client.images.remove(image.id, force=True)
                
        except APIError as e:
            print(f"Error removing image: {e}")
            
    elif action == 'build':
        try:
            client.images.get(IMAGE_NAME)
            print(f"Image {IMAGE_NAME} already exists.")
        except ImageNotFound:
            try:
                print("Building Docker image...")
                client.images.build(path='.', tag=IMAGE_NAME, rm=True)
                print("Image built successfully")
            except BuildError as e:
                print(f"Error building image: {e}")
            except APIError as e:
                print(f"Error during Docker API call: {e}")
        except APIError as e:
            print(f"Error checking image existence: {e}")
    else:
        print("Invalid action. Use 'remove' or 'build'.")

def run_container(index, port, detach):
    """Ejecuta un contenedor Docker con el índice y puerto proporcionados"""
    container_name = f"{CONTAINER_PREFIX}{index}"
    print(f"Starting container: {container_name}")

    volumes = {
        VOLUME_HOST_PATH: {'bind': VOLUME_CONTAINER_PATH, 'mode': 'rw'}
    }
    
    container = client.containers.run(
        IMAGE_NAME,
        name=container_name,
        network=NETWORK_NAME,
        detach=detach,
        ports={'5000/tcp': port},
        volumes=volumes  # Montar el volumen compartido
    )
    
    print(f"Container {container_name} started with ID: {container.id}")
    return container_name  # Devuelve el nombre del contenedor

def clean_volume_host(path):
    """Limpia el volumen en el host, eliminando todos los archivos y directorios."""
    if os.path.exists(path):
        print(f"Limpiando el volumen en el host: {path}...")
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Elimina archivos y enlaces simbólicos
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Elimina directorios y su contenido
            except Exception as e:
                print(f"Error al eliminar {file_path}: {e}")
    else:
        print(f"El volumen en el host {path} no existe. Creándolo...")
        os.makedirs(path)

def restart_process():
    """Reinicia el proceso eliminando contenedores e imágenes y reconstruyendo todo"""
    print("Updating .env file...")
    with open(ENV_FILE, "w") as file:
        file.write('PORT=3000\nCONTAINER_INDEX=0\n')

    manage_containers('stop')
    manage_containers('remove')
    manage_image('remove')  # Primero eliminar la imagen
    # manage_image('build')  # Luego construir la imagen


def open_logs_in_terminal(container_name):
    """Abre una nueva terminal con los logs del contenedor en Alacritty usando fish."""
    command = f"docker logs -f {container_name}; read -p 'Presiona enter para cerrar...' "
    subprocess.Popen(['alacritty', '-e', 'fish', '-c', command])
    
def manage_container_logs(flag):
    """Gestiona la apertura de terminales con los logs de contenedores según el flag indicado usando la API de Docker."""
    containers = client.containers.list(all=True, filters={"name": CONTAINER_PREFIX})
    running_containers = [container for container in containers if container.status == 'running']
    all_containers = containers

    if flag == '-l':
        print("Contenedores en ejecución:")
        for container in running_containers:
            print(container.name)
    
    if flag == '-ls':
        print("Contenedores:")
        for container in containers:
            print(container.name)

    elif flag == '-g':
        for container in running_containers:
            open_logs_in_terminal(container.name)

    elif flag == '-a':
        for container in all_containers:
            open_logs_in_terminal(container.name)

def main():
    """Función principal para gestionar contenedores Docker"""
    parser = argparse.ArgumentParser(description="Docker container management script.")
    parser.add_argument('-n', '--number', type=int, default=1, help="Number of containers to start")
    parser.add_argument('-b', '--build', action='store_true', help="Rebuild the Docker image and restart containers")
    parser.add_argument('-r', '--restart', action='store_true', help="Restart the process by stopping and removing containers and images, then building the image")
    parser.add_argument('-l', '--list', action='store_true', help="List all running containers")
    parser.add_argument('-ls', '--list-all', action='store_true', help="List all containers")
    parser.add_argument('-g', '--logs-running', action='store_true', help="Open logs in terminals for running containers")
    parser.add_argument('-a', '--logs-all', action='store_true', help="Open logs in terminals for all containers")
    parser.add_argument('-i', '--interactive-logs', action='store_true', help="Open logs in terminals for each container immediately after creation")
    parser.add_argument('-sip', '--stop-by-ip', type=str, help="Stop containers by their IP address")
    parser.add_argument('-sid', '--stop-by-index', type=int, help="Stop containers by their index")
    parser.add_argument('-u', '--run', type=int, help="Run the container with the specified index")
   
    args = parser.parse_args()

    if args.build:
        restart_process()
        
    if args.restart:
        restart_process()
        return
    
    if args.run:
        run_container_by_index(args.run)
        return
    

    if args.list or args.logs_running or args.logs_all or args.list_all :
        flag = '-l' if args.list else '-g' if args.logs_running else '-a' if args.logs_all else '-ls'
        manage_container_logs(flag)
        return

    if args.stop_by_ip:
        manage_containers('stop', container_ip=args.stop_by_ip)
        return
    
    if args.stop_by_index is not None:
        manage_containers('stop', container_index=args.stop_by_index)
        return

    create_network_if_not_exists()
    manage_image('build')
    port, start_index = read_env()
    
    # Limpia el volumen en el host antes de montarlo
    clean_volume_host(VOLUME_HOST_PATH)

    for i in range(start_index, start_index + args.number):
        container_name = run_container(i, port, True)
        port, start_index = update_env()
        time.sleep(5)

        if args.interactive_logs:
            open_logs_in_terminal(container_name)

if __name__ == '__main__':
    main()

