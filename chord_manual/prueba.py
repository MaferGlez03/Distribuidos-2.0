import hashlib
from storage import Database

def generate_id_( ip):
        """Genera un ID único basado en el hash de la IP y puerto."""
        # Obtener mi IP
        node_info = f"{ip}"
        return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)
response = generate_id_("nanda")
print(response)
a = (True, "aa")
print(a[0])