# Dependencias
import hashlib
import socket
import random

# Hashear la data
def set_id(data: str) -> int:
    """
    Hashea una cadena usando SHA-1 y devuelve un entero.
    """
    return int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 8)

# Obtener mi IP
def get_ip() -> str:
    """
    Obtiene la dirección IP local.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # Usamos una IP arbitraria que no se encuentra en nuestra red
            s.connect(('8.8.8.8', 80))
            ip_local = s.getsockname()[0]
            # ip_local = f'127.198.1.1{random.randint(10, 99)}'
            print("ip_local", ip_local)
        except Exception:
            ip_local = f'10.2.0.{random.randint(2, 10)}'  # Fallback a localhost
        return str(ip_local)