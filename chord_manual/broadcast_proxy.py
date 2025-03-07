import socket
import struct
import ipaddress
from subprocess import check_output
from multiprocessing import Process

LOCAL_ADDRS = [x for x in check_output(['hostname', '-i']).decode().strip().split(' ')]
IP_RECVORIGDSTADDR = 20
RESERVED_ADDRS = ['127.0.0.1']
MIN_PORT = 10000
PROCESS_AMOUNT = 5
BROADCAST_IP = "255.255.255.255"

def proxy(port, read_buffer=4196):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Habilitar broadcast

    server_address = ('', port)
    sock.bind(server_address)

    print(f"Listening on {server_address}")

    while True:
        data, _, _, address = sock.recvmsg(read_buffer)

        if address[0] in RESERVED_ADDRS or address[0] in LOCAL_ADDRS:
            continue

        print(f"Received data {data} from {address}, broadcasting...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(data, (BROADCAST_IP, port))
            print(f"Data broadcasted to {BROADCAST_IP}:{port}")

processes = []

for i in range(PROCESS_AMOUNT):
    p = Process(target=proxy, args=(MIN_PORT + i,))
    p.start()
    processes.append(p)

for p in processes:
    p.join()
