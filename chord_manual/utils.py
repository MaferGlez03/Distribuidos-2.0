import hashlib
    

def set_id(data: str) -> int:
    """
    Hashea una cadena usando SHA-1 y devuelve un entero.
    """
    return int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 8)

print(set_id("172.18.0.4"))
print(set_id("172.18.0.3"))
print(set_id("172.18.0.4"))