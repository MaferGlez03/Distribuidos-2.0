#region imports
from asyncio import Queue
import hashlib
import queue
import socket
import threading
import random
import time
import subprocess
from storage import Database
from handle_data import HandleData
from flexible_queue import FlexibleQueue
import os
#endregion

#region constants
TCP_PORT = 8000  # puerto de escucha del socket TCP
UDP_PORT = 8888  # puerto de escucha del socket UDP
VOLUME_CONTAINER_PATH = '/shared'  # Ruta dentro del contenedor
# Definición de operaciones Chord
JOIN = 'join'
CONFIRM_JOIN = 'conf_join'
FIX_FINGER = 'fix_fing'
FIND_FIRST = 'fnd_first'
FIND_FIRST_TOTAL = 'fnd_first_total'
REQUEST_DATA = 'req_data'
CHECK_PREDECESSOR = 'check_pred'
NOTIFY = 'notf'
UPDATE_PREDECESSOR = 'upt_pred'
UPDATE_FINGER = 'upd_fin'
UPDATE_SUCC = 'upd_suc'
UPDATE_LEADER = 'upd_leader'
UPDATE_FIRST = 'upd_first'
UPDATE_FIRST_TOTAL = 'upd_first_total'
DATA_PRED = 'dat_prd'
FALL_SUCC = 'fal_suc'

REPLICATE = 'repl'
PROPAGATION = 3
SUCC_PROPAGATION = 'succ_prop'
PRED_PROPAGATION = 'pred_prop'

REGISTER = 'reg'
LOGIN = 'log'
ADD_CONTACT = 'add_cnt'
LIST_PERSONAL_AGENDA = 'list_personal_agenda'
LIST_GROUP_AGENDA = 'list_group_agenda'
CREATE_GROUP = 'create_group'
DELETE_GROUP = 'delete_group'
LEAVE_GROUP = 'leave_group'
ADD_MEMBER = 'add_member'
REMOVE_MEMBER = 'remove_member'
LIST_GROUPS = 'list_groups'
CREATE_EVENT = 'create_event'
CREATE_GROUP_EVENT = 'create_group_event'
CREATE_INDIVIDUAL_EVENT ='create_individual_event'
CONFIRM_EVENT = 'confirm_event'
CANCEL_EVENT = 'cancel_event'
LIST_EVENTS = 'list_events'
LIST_EVENTS_PENDING = 'list_events_pending'
LIST_CONTACTS = 'list_contacts'
REMOVE_CONTACT = 'remove_contact'
LIST_MEMBER = 'list_member'
BROADCAST_IP = '255.255.255.255'
#endregion

class NodeReference:
    def __init__(self, ip: int, port: int, set: bool=False):
        self.id = ip if set else self.set_id(str(ip))
        self.ip = None if set else ip
        self.port = port
    
    # Hashear la data
    def set_id(self, data: str) -> int:
        """
        Hashea una cadena usando SHA-1 y devuelve un entero.
        """
        print("HASHING...")
        ret = int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 8)
        print("data: ", data, "return: ", ret)
        return ret
    def send_data_tcp(self, op, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # 🔹 Cambiar a TCP (SOCK_STREAM)
                s.connect((self.ip, self.port))  # 🔹 Conectar al servidor TCP
                s.sendall(f'{op}|{data}'.encode('utf-8'))  # 🔹 Enviar mensaje correctamente
                print(f"Mensaje enviado correctamente vía TCP. Operation: {op} Data: {data}")
                return s.recv(1024)
        except Exception as e:
            print(f"Mensaje fallido. Operation: {op} Data: {data} Error: {e}")
            return False

    def find_first(self):
        return self.send_data_tcp(FIND_FIRST, f'{self.id}')
    
    def request_data(self, id: int):
        return self.send_data_tcp(REQUEST_DATA, f'{id}')
    
    def notify(self, id: str):
        return self.send_data_tcp(NOTIFY, id)
    
    def update_finger(self, id: int, ip: str, port: int):
        return self.send_data_tcp(UPDATE_FINGER, f'{id}|{ip}|{port}')
    
    def list_group_agenda(self, group_id: int) -> str:
        response = self.send_data_tcp(LIST_GROUP_AGENDA, str(group_id))
        return response
    
    def register(self, id: int, name: str, email: str, password: str) -> str:
        response = self.send_data_tcp(REGISTER, f'{id}|{name}|{email}|{password}')
        return response
    def login(self, id:int,email: str, password: str) -> str:
        response = self.send_data_tcp(LOGIN, f'{id}|{email}|{password}')
        return response.decode()
    def list_personal_agenda(self, user_id: int) -> str:
        response = self.send_data_tcp(LIST_PERSONAL_AGENDA, str(user_id))
        return response
    
    def list_groups(self, user_id: int) -> str:
        response = self.send_data_tcp(LIST_GROUPS, str(user_id))
        return response
    
    def add_member_to_group(self, id:int,group_id: int, user_id: int) -> str:
        response = self.send_data_tcp(ADD_MEMBER, f'{id}|{group_id}|{user_id}')
        return response
    def remove_member_from_group(self,id:int, group_id: int, user_id: int) -> str:
        response = self.send_data_tcp(REMOVE_MEMBER, f'{id}|{group_id}|{user_id}')
        return response
    def list_member(self,user_id: int, group_id: int) -> str:
        response = self.send_data_tcp(LIST_MEMBER, f'{group_id}|{user_id}')
        return response
    
    def create_group(self, owner_id: int, name: str) -> str:
        response = self.send_data_tcp(CREATE_GROUP, f'{name}|{owner_id}')
        return response
    def delete_group(self, owner_id: int, name: str) -> str:
        response = self.send_data_tcp(DELETE_GROUP, f'{name}|{owner_id}')
        return response
    def leave_group(self, owner_id: int, name: str) -> str:
        response = self.send_data_tcp(LEAVE_GROUP, f'{name}|{owner_id}')
        return response
    def list_contacts(self, user_id: int) -> str:
        response = self.send_data_tcp(LIST_CONTACTS, str(user_id))
        return response
    def remove_contact(self, user_id: int, contact_name: str) -> str:
        response = self.send_data_tcp(REMOVE_CONTACT, f'{user_id}|{contact_name}')
        return response
    def add_contact(self, user_id: int, contact_name: str) -> str:
        response = self.send_data_tcp(ADD_CONTACT, f'{user_id}|{contact_name}')
        return response
    def list_events_pending(self, user_id: int) -> str:
        response = self.send_data_tcp(LIST_EVENTS_PENDING, str(user_id))
        return response
    def list_events(self, user_id: int) -> str:
        response = self.send_data_tcp(LIST_EVENTS, str(user_id))
        return response
    def cancel_event(self, event_id: int) -> str:
        response = self.send_data_tcp(CANCEL_EVENT, str(event_id))
        return response
    def confirm_event(self, event_id: int) -> str:
        response = self.send_data_tcp(CONFIRM_EVENT, str(event_id))
        return response
    def create_event(self, event_id: int, name: str, date: str, privacy: str, group_id=None) -> str:
        response = self.send_data_tcp(CREATE_EVENT, f'{event_id}|{name}|{date}|{privacy}|{group_id}')
        return response
    def create_group_event(self, event_id: int, name: str, date: str, group_id=None) -> str:
        response = self.send_data_tcp(CREATE_GROUP_EVENT, f'{event_id}|{name}|{date}|{group_id}')
        return response
    def create_individual_event(self, event_id: int, name: str, date: str, owner_id: int, privacy: str, group_id=None) -> str:
        response = self.send_data_tcp(CREATE_INDIVIDUAL_EVENT, f'{event_id}|{name}|{date}|{owner_id}|{privacy}|{group_id}')
        return response

class ChordNode:
    def __init__(self):
        self.ip = self.get_ip()
        self.id = self.generate_id()
        self.node_first = self._acquire_lock()
        self.tcp_port = TCP_PORT
        self.udp_port = UDP_PORT
        self.predecessor = NodeReference(self.ip, self.tcp_port)
        self.successor = NodeReference(self.ip, self.tcp_port)
        self.ip_table = {} # IPs table: {ID: {IP, port}}
        self.finger_table = self.create_finger_table() # Finger table: {ID: Owner}
        self.leader = False
        self.first = False
        self.repli_pred = ''
        self.repli_pred_pred = ''
        self.actual_first_id = self.id

        self.handler_data = HandleData(self.id)
        self.finger_update_queue = queue.Queue()# Cola de actualizaciones de finger table
        self.finger_update_fall_queue = queue.Queue() # Cola de actualizaciones de finger table cuando se cae un nodo
       
        self.db = Database()
        self.succ_queue = self.init_queue()
        self.pred_queue = self.init_queue()

        threading.Thread(target=self.start_tcp_server).start()
        threading.Thread(target=self.start_broadcast).start()
        threading.Thread(target=self.handle_finger_table).start()
        threading.Thread(target=self.handle_finger_table_update).start()

        self.join()
        
    def start_tcp_server(self):
        """Iniciar el servidor TCP."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.tcp_port))
            print(f'Socket TCP binded to ({self.ip}, {self.tcp_port})')
            s.listen()

            # Se queda escuchando cualquier mensaje entrante
            while True:
                time.sleep(1)
                conn, addr = s.accept()
                client = threading.Thread(target=self._handle_client_tcp, args=(conn, addr))
                client.start()

    def _handle_client_tcp(self, conn: socket.socket, addr: tuple):
        data = conn.recv(1024).decode().split('|') # operation | id | port
        option = data[0]
        if option == '':
            return
        id = data[1]
        response = f'ok'
        print("ANALIZANDO MENSAJE EN TCP: ", option)
        
        
        if option == FIX_FINGER:
            self.finger_update_queue.put((id, TCP_PORT))
            return
        
        if option == REPLICATE:
            if id == self.predecessor.id:
                self.db_pred = data[2]
            elif id == self.succesor.id:
                self.db_succ = data[2]

        elif option == REGISTER:
            id = int(data[1])
            name = data[2]
            email = data[3]
            password = data[4]
            # Procesar el registro
            response = self.register(id, name, email, password)
        elif option == LOGIN:
            # Iniciar sesión
            id = data[1]
            email = data[2]
            password = data[3]
            response = self.login_user(id,email, password)
        elif option == CREATE_EVENT:
            # Crear un evento
            event_id = int(data[1])
            name = data[2]
            date = data[3]
            privacy = data[4]
            group_id = int(data[5]) if len(data) > 5 else None
            response = self.create_event(event_id, name, date, privacy, group_id)
        elif option == CREATE_GROUP_EVENT:
            # Crear un evento
            event_id = int(data[1])
            name = data[2]
            date = data[3]
            group_id = int(data[4]) if len(data) > 4 else None
            response = self.create_group_event(event_id, name, date, group_id)
        elif option == CREATE_INDIVIDUAL_EVENT:
            # Crear un evento
            event_id = int(data[1])
            name = data[2]
            date = data[3]
            group_id = int(data[4]) if len(data) > 4 else None
            response = self.create_individual_event(event_id, name, date, group_id)
        elif option == CONFIRM_EVENT:
            # Confirmar un evento
            event_id = int(data[1])
            response = self.confirm_event(event_id)
        elif option == CANCEL_EVENT:
            # Cancelar un evento
            event_id = int(data[1])
            response = self.cancel_event(event_id)
        elif option == LIST_EVENTS:
            # Listar eventos de un usuario
            user_id = int(data[1])
            response = self.list_events(user_id)
        elif option == LIST_EVENTS_PENDING:
            # Listar eventos de un usuario
            user_id = int(data[1])
            response = self.list_events_pending(user_id)
        elif option == ADD_CONTACT:
            # Agregar un contacto
            user_id = int(data[1])
            contact_name = data[2]
            response = self.add_contact(user_id, contact_name)
        elif option == REMOVE_CONTACT:
            # Eliminar un contacto
            user_id = int(data[1])
            contact_name = data[2]
            response = self.remove_contact(user_id, contact_name)
        elif option == LIST_CONTACTS:
            # Listar contactos de un usuario
            user_id = int(data[1])
            response = self.list_contacts(user_id)
        elif option == CREATE_GROUP:
            # Crear un grupo
            name = data[1]
            owner_id = int(data[2])
            response = self.create_group(owner_id, name)
        elif option == DELETE_GROUP:
            # Crear un grupo
            name = data[1]
            owner_id = int(data[2])
            response = self.delete_group(owner_id, name)
        elif option == LEAVE_GROUP:
            # Crear un grupo
            name = data[1]
            owner_id = int(data[2])
            response = self.leave_group(owner_id, name)
        elif option == ADD_MEMBER:
            # Agregar un miembro a un grupo
            id =int(data[1])
            group_id = int(data[2])
            user_id = int(data[3])
            response = self.add_member_to_group(id,group_id, user_id)
        elif option == REMOVE_MEMBER:
            # Agregar un miembro a un grupo
            id =int(data[1])
            group_id = int(data[2])
            user_id = int(data[3])
            response = self.remove_member_from_group(id,group_id, user_id)
        elif option == LIST_GROUPS:
            # Listar grupos de un usuario
            user_id = int(data[1])
            response = self.list_group(user_id)
        elif option == LIST_MEMBER:
            # Listar grupos de un usuario
            user_id = int(data[2])
            group_id = int(data[1])
            response = self.list_member(user_id,group_id)
        elif option == LIST_PERSONAL_AGENDA:
            # Listar agenda personal
            user_id = int(data[1])
            response = self.list_personal_agenda(user_id)
        elif option == LIST_GROUP_AGENDA:
            # Listar agenda grupal
            group_id = int(data[1])
            response = self.list_group_agenda(group_id)
        elif option == REQUEST_DATA:
            id = int(data[1])
            response = self.handler_data.data(True, id)

        elif option == CHECK_PREDECESSOR:
            response = (self.handler_data.data(False) + self.predecessor.ip) #!AQUI EL OBJETIVO ES OBTENE LA DATA DE MI PREDECESOR

            # si somos al menos 3 nodos, le mando a mi sucesor la data de mi predecesor
            if self.predecessor.id != self.successor.id:
                self.successor.send_data_tcp(DATA_PRED, self.repli_pred)
                
        elif option == DATA_PRED:
            data_ = data[1]
            self.repli_pred_pred = data_ #!AQUI TAL VEZ HAY Q CAMBIAR LA LOGICA POR LA FORMA DE REPLICAR

        elif option == FALL_SUCC:
            ip = data[1]
            port = int(data[2])
            self.successor = NodeReference(ip, port)
            response = f'ok'
            # pido data a mi sucesor al actualizar mi posicion
            self.request_succ_data(succ=True) #!ESTO es lo del balanceo de carga
            # si se cayo mi sucesor, le digo a su sucesor que soy su  nuevo predecesor
            self.successor.send_data_tcp(UPDATE_PREDECESSOR, f'{self.ip}|{self.tcp_port}')
        elif option == UPDATE_PREDECESSOR:
            ip = data[1]
            port = int(data[2])
            self.predecessor = NodeReference(ip, port)
            
        
        elif option == SUCC_PROPAGATION:
            propagation = int(data[2]) - 1
            self.pred_queue.replace_at(id, propagation)

            self.succesor.send_data_tcp(option, f'{self.id}|{PROPAGATION}')

            # Enviar al siguiente si todavia el valor de propagacion > 0
            if propagation > 0:
                self.succesor.send_data_tcp(option, f'{id}|{propagation}')

        elif option == PRED_PROPAGATION:
            propagation = int(data[2]) - 1
            self.succ_queue.replace_at(id, propagation)

            self.predecessor.send_data_tcp(option, f'{self.id}|{PROPAGATION}')

            # Enviar al siguiente si todavia el valor de propagacion > 0
            if propagation > 0:
                self.predecessor.send_data_tcp(option, f'{id}|{propagation}')
        
        else:
            # Operación no reconocida
            response = "Invalid operation"

    # Enviar respuesta al cliente
        conn.sendall(response.encode())
        conn.close()

        print("conn, addr, data", conn, addr, data)
        print("option, info, ip, port", option, id)

    def check_predecessor(self):
        while True:
            if self.predecessor.id != self.id:
                
                data = self.predecessor.send_data_tcp(CHECK_PREDECESSOR, f'0|0')
                if data:
                    self.repli_pred= data.decode()
                    ip_pred_pred = self.repli_pred.split('|')[-1]
                else:
                    print(f"El servidor {self.predecessor.ip} se ha desconectado")
                    #!Replicar en la bd la info del predecesor
                    
                    self.send_data_broadcast(UPDATE_FINGER, f"{self.predecessor.id}|{self.ip}|{TCP_PORT}")
                    if self.predecessor.id != self.successor.id: #somos al menos 3
                        try:  
                            #tratamos de conectarnos con el predecesor de nuestro predecesor para comunicarle que se cayo su sucesor
                            #seguimos el mismo proceso
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                              s.connect((ip_pred_pred, TCP_PORT))
                              s.settimeout(5)
                              s.sendall(f'{FALL_SUCC}|{self.ip}|{self.tcp_port}')
                              s.recv(1024).decode()

                        except:
                            pass

    def send_data_broadcast(self, op, data):
        """
        Envía un mensaje por broadcast utilizando UDP.
        
        :param op: Operación a enviar (str).
        :param data: Datos a enviar (str).
        """
        try:
            # Crear un socket UDP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Habilitar el envío de broadcast
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                
                # Construir el mensaje
                mensaje = f"{op}|{data}".encode('utf-8')
                
                # Enviar el mensaje por broadcast
                s.sendto(mensaje, (BROADCAST_IP, self.udp_port))
                print(f"Mensaje enviado por broadcast. Operation: {op} Data: {data}")
        except Exception as e:
            print(f"Error al enviar mensaje por broadcast. Operation: {op} Data: {data} Error: {e}")

    def start_broadcast(self):
        """
        Escucha mensajes de broadcast en el puerto especificado.
        
        :param puerto: Puerto donde escuchar el broadcast.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Permitir reutilizar el puerto
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                # Vincular el socket al puerto
                s.bind(("", self.udp_port))  # "" significa que escucha en todas las interfaces
                
                print(f"[+] Escuchando broadcast en el puerto {self.udp_port}...")
                
                while True:
                    time.sleep(1)
                    # Recibir datos
                    datos, direccion = s.recvfrom(1024)
                    mensaje = datos.decode('utf-8')
                    thread = threading.Thread(target=self.handle_broadcast, args=(mensaje, direccion))
                    thread.start()
        except Exception as e:
            print(f"[!] Error al recibir broadcast: {e}")

    def handle_broadcast(self, mensaje, direccion):
        # Maneja el mensaje entrante 
        data = mensaje.split('|') # operation | id | port | (other_id) | (other_port) 
        option = data[0]
        if option == '':
            return
        if data[1] != None:
            id = int(data[1])
            port = int(data[2])
        print("ANALIZANDO MENSAJE: ", option)
        address = direccion[0]

        if option == JOIN:
            # No hacer nada si recibo la operacion de mi mismo
            if self.id == id:
                pass
            # Me estoy uniendo a una red donde solo hay un nodo
            elif self.id == self.successor.id and self.id == self.predecessor.id:
                print(f"Me estoy uniendo a una red donde solo hay un nodo({self.id})")
                # Actualiza mi self.successor a id
                op = UPDATE_SUCC
                data = f'{self.id}|{self.tcp_port}|{id}|{port}'
                self.send_data_broadcast(op, data)
                
                # Actualiza mi self.predecessor a id
                op = UPDATE_PREDECESSOR
                data = f'{self.id}|{self.tcp_port}|{id}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.sucesor a self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.id}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.predecesor a self.id
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.id}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualizo first y leader
                if self.id > id:
                    self.set_leader(self.id, self.tcp_port, id, port)
                    self.set_first(id, port, self.id, self.tcp_port)
                elif self.id < id:
                    self.set_first(self.id, self.tcp_port, id, port)
                    self.set_leader(id, port, self.id, self.tcp_port)

                print("self.ip, self.predecessor.ip, self.successor.ip: ", self.ip, self.predecessor.ip, self.successor.ip)
        # Hay 2 nodos o mas
            # Esta entre yo y mi predecesor
            elif self.id > id and self.predecessor.id < id:
                print(f"Esta entre yo({self.id}) y mi predecesor({self.predecessor.id})")
                # Actualiza mi sucesor por el nodo entrante
                op = UPDATE_SUCC
                data = f'{self.predecessor.id}|{self.predecessor.port}|{id}|{port}'
                self.send_data_broadcast(op, data)
                
                # Actualiza mi predecesor por el nodo entrante
                op = UPDATE_PREDECESSOR
                data = f'{self.id}|{self.tcp_port}|{id}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.sucesor a self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.id}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.predecesor a self.id
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.predecessor.id}|{self.predecessor.port}'
                self.send_data_broadcast(op, data)
                print("self.ip, self.predecessor.ip, self.successor.ip: ", self.ip, self.predecessor.ip, self.successor.ip)
            
            # Es menor que yo y soy el first
            elif self.id > id and self.first: 
                print(f"Es menor que yo({self.id}) y soy el first({self.first})")
                # Actualiza el predecesor del nodo entrante por self.predecesor
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.predecessor.id}|{self.predecessor.port}'
                self.send_data_broadcast(op, data)
                
                # Actualiza el sucesor del nodo entrante por self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.id}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza mi predecesor por el nodo entrante
                op = UPDATE_PREDECESSOR
                data = f'{self.id}|{self.tcp_port}|{id}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza el sucesor de mi predecesor por el nodo entrante
                op = UPDATE_SUCC
                data = f'{self.predecessor.id}|{self.predecessor.port}|{id}|{port}'
                self.send_data_broadcast(op, data)

                # Actualizo first
                self.set_first(id, port, self.id, self.tcp_port)

                print("self.ip, self.predecessor.ip, self.successor.ip: ", self.ip, self.predecessor.ip, self.successor.ip)
            
            # Es mayor que yo y soy el leader
            elif self.id < id and self.leader:
                print(f"Es mayor que yo({self.id}) y soy el leader({self.leader})")
                # Actualiza el sucesor del nodo entrante por mi sucesor
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.successor.id}|{self.successor.port}'
                self.send_data_broadcast(op, data)
                
                # Actualiza el predecesor del nodo entrante por mi
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.id}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza mi sucesor por el nodo entrante
                op = UPDATE_SUCC
                data = f'{self.id}|{self.tcp_port}|{id}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza el predecesor de mi sucesor por el nodo entrante
                op = UPDATE_PREDECESSOR
                data = f'{self.successor.id}|{self.successor.port}|{id}|{port}'
                self.send_data_broadcast(op, data)

                # Actualizo leader
                self.set_leader(id, port, self.id, self.tcp_port)
                
                print("self.ip, self.predecessor.ip, self.successor.ip: ", self.ip, self.predecessor.ip, self.successor.ip)
        
        elif option == UPDATE_SUCC:
            new_id = int(data[3])
            new_port = int(data[4])
            print("CHECK successor: ", self.id, id, self.id == id, new_id, new_port)
            if self.id == id:
                print("UPDATE_SUCC")
                self.successor = NodeReference(new_id, new_port, True)

        elif option == UPDATE_PREDECESSOR:
            new_id = int(data[3])
            new_port = int(data[4])
            print("CHECK PREDECESSOR: ", self.id, id, self.id == id, new_id, new_port)
            if self.id == id:
                print("UPDATE_PREDECESSOR")
                self.predecessor = NodeReference(new_id, new_port, True)
                
        elif option == FIX_FINGER:
            
            if address != self.ip:
                #el nodo que entra es mayor que yo, lo pongo en mi lista para actualizar mi finger teble.
                node = NodeReference(address, TCP_PORT)
                # if self.id < self.generate_id_(address):
                #     print("soy menor")
                self.finger_update_queue.put((address, TCP_PORT))
                node.send_data_tcp(FIX_FINGER, self.ip)
                        
                # #el nodo que entra es mayor que yo, mando una solicitud para que me ponga en su finger table
                # else:
                #     print("soy mayor")
                #     if (self.actual_first_id == self.generate_id_(node.ip)):
                #         self.finger_update_queue.put((address, TCP_PORT))
                #     node.send_data_tcp(FIX_FINGER, self.ip)
            print("Solicitud propia")
            
        elif option == UPDATE_FIRST:
            old_id = int(data[3])
            print(f"CONFIRMADO: {id} es el nuevo first y {old_id} ya no es first")
            self.actual_first_id = id
            if self.id == id: 
                self.first = True
            elif self.id == old_id: 
                self.first = False

        elif option == UPDATE_LEADER:
            old_id = int(data[3])
            print(f"CONFIRMADO: {id} es el nuevo lider y {old_id} ya no es lider")

            if self.id == id: 
                self.leader = True
            elif self.id == old_id: 
                self.leader = False

        elif option == FIND_FIRST_TOTAL:
            if self.first:
                self.get_first(self.id, self.tcp_port)
            
        elif option == UPDATE_FIRST_TOTAL:
            self.actual_first_id = id
            
        elif option == UPDATE_FINGER:
            port_= data[3]
            self.finger_update_fall_queue.put((id,port,port_)) #aqui port en realidad es un ip

    def join(self):
        op = JOIN
        data = f'{self.id}|{self.tcp_port}'
        self.send_data_broadcast(op, data)
        time.sleep(5)
        self.request_first()
        time.sleep(5)
        self.send_data_broadcast(FIX_FINGER, f'0|0')
        self.send_data_propagation()

    def create_finger_table(self):
        table = {}
        id = self.id
        for i in range(8):
            self.ip_table[id] = self.ip
            table[(id + 2**i) % 256] = NodeReference(self.ip,self.tcp_port)
        return table

    def handle_finger_table(self):   
        """
        Hilo que maneja las actualizaciones de la tabla de fingers.
        """
        while True:
            try:
                ip,port = self.finger_update_queue.get()
                self.fix_finger_table(NodeReference(ip, port))
                print("Finger table arreglada")
            finally:
                self.finger_update_queue.task_done()
                self.print_finger_table()
    def handle_finger_table_update(self):   
        """
        Hilo que maneja las actualizaciones de la tabla de fingers.
        """
        while True:
    
            try:
                id,ip,port = self.finger_update_fall_queue.get()
                #print(node)
                
                self.fix_finger_table(NodeReference(ip, port),id)
                print("Finger table arreglada")

                
            finally:
                self.finger_update_fall_queue.task_done()
                self.print_finger_table()
            

    def fix_finger_table(self,node:NodeReference, id = None):
        """
        Corrige la tabla de fingers si un nodo deja de responder o cambia la red.
        """
        print("[!] Verificando y corrigiendo tabla de fingers...")
        for i in range(8):
            finger_id = (self.id + 2**i) % 256
            if id == None:
                #si el nodo nuevo es menor que el que se esta haciendo cargo
                # print(f"  Yo{self.id} Me actualizo con {node.id}")
                # print(f"fingerid: {finger_id}")
                # print(f" actual first: {self.actual_first_id}")
                if node.id < self.finger_table[finger_id].id:
                    #si me puedo hacer cargo 
                    print(f" nodo encargado del finger {finger_id} es {self.finger_table[finger_id].id} ")
                    if (finger_id) <= node.id  :
                        self.finger_table[finger_id]= node
                        print(f"[+] Finger {finger_id} actualizado a {node.id}")

                    elif self.actual_first_id== node.id and self.finger_table[finger_id].id < (finger_id) :
                        self.finger_table[finger_id] = node
                        print(f"[+] Finger {finger_id} actualizado a {node.id}")


                # si el nodo es mayor que el que se esta haciendo cargo, pero este se esta haciendo cargo de un dato con id mas grande. 
                elif self.finger_table[finger_id].id < (finger_id) and finger_id<node.id:
                    self.finger_table[finger_id]= node
                    print(f"[+] Finger {finger_id} actualizado a {node.id}")
            else:
                if self.finger_table[finger_id]==id:
                    self.finger_table[finger_id]= node
                
    

    def print_finger_table(self):
        print(f" Nodo: {self.id} FINGER TABLE. FIRST: {self.first}. LEADER: {self.leader}")
        for i in range(8):
            finger_id = (self.id + 2**i) % 256
            print(f"id: {finger_id} |||| owner: {self.finger_table[finger_id].id} \n")
            
    def verificar_ip_activa(self, ip, puerto):
        """
        Verifica si una IP está activa en un puerto TCP específico.

        :param ip: Dirección IP a verificar (str).
        :param puerto: Puerto TCP a verificar (int).
        :return: True si la IP está activa en el puerto, False en caso contrario.
        """
        # Crear un socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)  # Tiempo de espera máximo en segundos

        try:
            # Intentar conectar al puerto
            resultado = sock.connect_ex((ip, puerto))
            if resultado == 0:
                print(f"[+] La IP {ip} está activa en el puerto {puerto}.")
                print(f"{self.id}|{self.predecessor.id}|{self.successor.id}")
                print(f"First: {self.first} | Leader: {self.leader}")
                return True
            else:
                print(f"[-] La IP {ip} no responde en el puerto {puerto}. Código de error: {resultado}")
                return False
        except Exception as e:
            print(f"[!] Error al conectar con {ip}:{puerto}. Detalles: {e}")
            return False
        finally:
            # Cerrar el socket
            sock.close()

    def _closest_preceding_node(self, id) -> NodeReference:
        """Devuelve el nodo más cercano a un ID en la finger table."""
        for i in range(8):
            if (self.id + (2**i) % 256) > id:
                return self.finger_table[i-1]

    def find_first(self) -> bytes:
        """Buscar el primer nodo."""
        if self.leader:
            return f'{self.successor.ip}|{self.successor.port}'.encode()

        response = self.finger_table[-1].find_first()
        return response
    
    def request_succ_data(self, succ=False, pred=False):
        """Preguntar a mi sucesor por data."""
        if self.successor.id != self.id:
            if succ:
                response_succ = self.successor.request_data(self.id).decode()
                self.handler_data.create(response_succ)

        if pred:
            response_pred = self.predecessor.request_data(self.id).decode()
            self.handler_data.create(response_pred)
        
    def set_first(self, id, port, old_id, old_port):
        print(f"{id} es el nuevo first y {old_id} ya no es first")
        op = UPDATE_FIRST
        data = f'{id}|{port}|{old_id}|{old_port}'
        self.send_data_broadcast(op, data)

    def set_leader(self, id, port, old_id, old_port):
        print(f"{id} es el nuevo lider y {old_id} ya no es lider")
        op = UPDATE_LEADER
        data = f'{id}|{port}|{old_id}|{old_port}'
        self.send_data_broadcast(op, data)
    
    def request_first(self):
        print("BUSCANDO FIRST")
        op = FIND_FIRST_TOTAL
        data = f'{0}|{0}'
        self.send_data_broadcast(op, data)

    def get_first(self, id, port):
        print(f"FIRST ACTUAL: {id}")
        op = UPDATE_FIRST_TOTAL
        data = f'{id}|{port}'
        self.send_data_broadcast(op, data)

    def get_ip(self) -> str:
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
        
    def id_to_ip(self, id):
        return self.ip_table[id]

    def generate_id(self):
        """Genera un ID único basado en el hash de la IP y puerto."""
        # Obtener mi IP
        node_info = f"{self.ip}"
        return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)
    
    def generate_id_(self, ip):
        """Genera un ID único basado en el hash de la IP y puerto."""
        # Obtener mi IP
        node_info = f"{ip}"
        return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)
    
    def send_data_propagation(self):
        self.predecessor.send_data_tcp(PRED_PROPAGATION, f'{self.id}|{PROPAGATION}')
        self.succesor.send_data_tcp(SUCC_PROPAGATION, f'{self.id}|{PROPAGATION}')

    def init_queue(self):
        q = FlexibleQueue()
        for _ in range(PROPAGATION):
            q.push_front(self.id)
        return q
    
    def _acquire_lock(self):
        """Intenta adquirir el lock y devuelve True si este nodo es el primero."""
        lock_file = os.path.join(VOLUME_CONTAINER_PATH, "lockfile")

        try:
            # Intenta crear el archivo de lock (modo exclusivo)
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, 'w') as f:
                f.write(f"lock{self.id}")  # Escribe algo en el archivo

            # Si llegamos aquí, este nodo es el primero
            print(f"NODO {self.id} adquirió el lock!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!.")
            return True
        except FileExistsError:
            # Si el archivo ya existe, otro nodo ya adquirió el lock
            print(f"NODO {self.id} no es el primero!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return False

#region DB

    def replicate(self):
        op = REPLICATE
        data = f'{self.id}|{self.db}'
        self.predecessor.send_data_tcp(op, data)
        self.succesor.send_data_tcp(op, data)

    def register(self, id: int, name: str, email: str, password: str) -> str:
        if id < self.id and not self.first:
            # Reenviar al "first"
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.register(id, name, email, password)
        else:
            # Registrar localmente
            return self._register(id, name, email, password)
    def _register(self, id: int, name: str, email: str, password: str) -> str:
        if (id < self.id) or (id > self.id and self.leader):
            # Registrar en la BD local
            success = self.db.register_user(name, email, password)[0]
            return ("User registered", success[1]) if success else ("Failed to register user", success[1])
        else:
            # Reenviar al nodo más cercano
            closest_node = self._closest_preceding_node(id)
            return closest_node.register(id, name, email, password)
    def login_user(self, id: int, name: str, password: str) -> str:
        if id < self.id and not self.first:
            # Reenviar al "first"
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.login(id, name, password)
        else:
            # Registrar localmente
            return self._login_user(id, name, password)
    def _login_user(self, id: int, name: str, password: str) -> str:
        if (id < self.id) or (id > self.id and self.leader):
            # Registrar en la BD local
            success = self.db.login_user(name, password)[0]
            return ("User logged", success[1]) if success else ("Failed to log user in", success[1])
        else:
            # Reenviar al nodo más cercano
            closest_node = self._closest_preceding_node(id)
            return closest_node.login(id, name, password)
    def create_event(self, event_id: int, name: str, date: str, privacy: str, group_id=None) -> str:
        if event_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.create_event(event_id, name, date, privacy, group_id)
        else:
            return self._create_event(event_id, name, date, privacy, group_id)
    def _create_event(self, event_id: int, name: str, date: str, privacy: str, group_id=None) -> str:
        if (event_id < self.id) or (event_id > self.id and self.leader):
            success = self.db.create_event(
                name, date, event_id, privacy, group_id)
            return f"Event created: {name}" if success else f"Failed to create event {name}"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.create_event(event_id, name, date, privacy, group_id)
    def create_group_event(self, event_id: int, name: str, date: str, group_id=None) -> str:
        if event_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.create_group_event(event_id, name, date, group_id)
        else:
            return self._create_group_event(event_id, name, date, group_id)
    def _create_group_event(self, event_id: int, name: str, date: str, group_id=None) -> str:
        if (event_id < self.id) or (event_id > self.id and self.leader):
            success = self.db.create_group_event(name, date, event_id, group_id)
            return f"Event created: {name}" if success else f"Failed to create event {name}"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.create_group_event(event_id, name, date, group_id)
    def create_individual_event(self, event_id: int, name: str, date: str, group_id=None) -> str:
        if event_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.create_individual_event(event_id, name, date, group_id)
        else:
            return self._create_individual_event(event_id, name, date, group_id)
    def _create_individual_event(self, event_id: int, name: str, date: str, group_id=None) -> str:
        if (event_id < self.id) or (event_id > self.id and self.leader):
            success = self.db.create_individual_event(name, date, event_id, group_id)
            return f"Event created: {name}" if success else f"Failed to create event {name}"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.create_individual_event(event_id, name, date, group_id)
    def confirm_event(self,user_id:int, event_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.confirm_event(user_id,event_id)
        else:
            return self._confirm_event(user_id,event_id)
    def _confirm_event(self,user_id:int, event_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            success = self.db.confirm_event(event_id)
            return "Event confirmed" if success else "Failed to confirm event"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.confirm_event(user_id,event_id)
    def cancel_event(self, user_id:int,event_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.cancel_event(user_id, event_id)
        else:
            return self._cancel_event(user_id, event_id)
    def _cancel_event(self, user_id:int, event_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            success = self.db.cancel_event(event_id)
            return "Event canceled" if success else "Failed to cancel event"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.cancel_event(user_id, event_id)
    def list_events(self, user_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.list_events(user_id)
        else:
            return self._list_events(user_id)
    def _list_events(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            events = self.db.list_events(user_id)
            events_list = []
            for event in events:
              events_list.append({
                'id': event.id,
                'name': event.name,
                'date': event.date.strftime('%Y-%m-%d'),
                'owner_id': event.owner_id,
                'privacy': event.privacy,
                'group_id': event.group_id,
                'status': event.status
                })
            return "\n".join([str(event) for event in events_list])
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_events(user_id)
    def list_events_pending(self, user_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.list_events_pending(user_id)
        else:
            return self._list_events_pending(user_id)
    def _list_events_pending(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            events = self.db.list_events_pending(user_id)
            events_list = []
            for event in events:
              events_list.append({
                'id': event.id,
                'name': event.name,
                'date': event.date.strftime('%Y-%m-%d'),
                'owner_id': event.owner_id,
                'privacy': event.privacy,
                'group_id': event.group_id,
                'status': event.status
                })
            return "\n".join([str(event) for event in events_list])
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_events_pending(user_id)
    def add_contact(self, user_id: int, contact_name: str, owner_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.add_contact(user_id, contact_name, owner_id)
        else:
            return self._add_contact(user_id, contact_name, owner_id)
    def _add_contact(self, user_id: int, contact_name: str, owner_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            success = self.db.add_contact(user_id, contact_name, owner_id)
            return "Contact added" if success else "Failed to add contact"
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.add_contact(user_id, contact_name, owner_id)
    def remove_contact(self, user_id: int, contact_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.remove_contact(user_id, contact_id)
        else:
            return self._remove_contact(user_id, contact_id)
    def _remove_contact(self, user_id: int, contact_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            success = self.db.delete_contact(contact_id)
            return "Contact removed" if success else "Failed to remove contact"
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.remove_contact(user_id, contact_id)
    def list_contacts(self, user_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.list_contacts(user_id)
        else:
            return self._list_contacts(user_id)
    def _list_contacts(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            contacts = self.db.list_contacts(user_id)
            return "\n".join(contacts)
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_contacts(user_id)
    def create_group(self, owner_id:int, name: str) -> str:
        if owner_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.create_group(owner_id, name)
        else:
            return self._create_group(owner_id, name)
    def _create_group(self, owner_id:int, name: str) -> str:
        if (owner_id < self.id) or (owner_id > self.id and self.leader):
            success = self.db.create_group(name, owner_id)
            return "Group created" if success else "Failed to create group"
        else:
            closest_node = self._closest_preceding_node(owner_id)
            return closest_node.create_group(owner_id, name)
    def delete_group(self, owner_id: int, name: str,) -> str:
        if owner_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.delete_group(owner_id, name)
        else:
            return self._delete_group(owner_id, name)
    def _delete_group(self, owner_id:int, name: str) -> str:
        if (owner_id < self.id) or (owner_id > self.id and self.leader):
            success = self.db.delete_group(name)
            return "Group deleted" if success else "Failed to delete group"
        else:
            closest_node = self._closest_preceding_node(owner_id)
            return closest_node.delete_group(owner_id, name)
    def leave_group(self, name: str, owner_id: int) -> str:
        if owner_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.leave_group(owner_id, name)
        else:
            return self._leave_group(owner_id, name)
    def _leave_group(self, owner_id:int, name: str) -> str:
        if (owner_id < self.id) or (owner_id > self.id and self.leader):
            success = self.db.leave_group(name)
            return "Group leaved" if success else "Failed to leave group"
        else:
            closest_node = self._closest_preceding_node(owner_id)
            return closest_node.leave_group(owner_id, name)
    def add_member_to_group(self,id:int, group_id: int, user_id: int,role) -> str:
        if id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.add_member_to_group(id,group_id, user_id, role)
        else:
            return self._add_member_to_group(id,group_id, user_id, role)
    def _add_member_to_group(self,id:int, group_id: int, user_id: int,role) -> str:
        if (id < self.id) or (id > self.id and self.leader):
            success = self.db.add_member_to_group(group_id, user_id, role)
            return "Member added" if success else "Failed to add member"
        else:
            closest_node = self._closest_preceding_node(id)
            return closest_node.add_member_to_group(id,group_id, user_id,role)
    def remove_member_from_group(self,id:int, group_id: int, user_id: int) -> str:
        if id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.remove_member_from_group(id,group_id, user_id)
        else:
            return self._remove_member_from_group(id,group_id, user_id)
    def _remove_member_from_group(self,id:int, group_id: int, user_id: int) -> str:
        if (id < self.id) or (id > self.id and self.leader):
            success = self.db.remove_member_from_group(group_id, user_id)
            return "Member removed" if success else "Failed to remove member"
        else:
            closest_node = self._closest_preceding_node(id)
            return closest_node.remove_member_from_group(id,group_id, user_id)
    def list_group(self, user_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.list_groups(user_id)
        else:
            return self._list_group(user_id)
    def _list_group(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            agenda = self.db.list_groups(user_id)
            groups_list = [{'id': g[0], 'name': g[1]} for g in agenda]
            return "\n".join(groups_list)
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_groups(user_id)
    def list_member(self, user_id: int, group_id:int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.list_member(user_id, group_id)
        else:
            return self._list_member(user_id, group_id)
    def _list_member(self, user_id: int, group_id:int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            agenda = self.db.list_members(group_id)
            return "\n".join(agenda)
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_member(user_id,group_id)
    def list_personal_agenda(self, user_id: int) -> str:
        if user_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.list_personal_agenda(user_id)
        else:
            return self._list_personal_agenda(user_id)
    def _list_personal_agenda(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            agenda = self.db.list_personal_agenda(user_id)
            return "\n".join(agenda)
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_personal_agenda(user_id)
    def list_group_agenda(self, group_id: int) -> str:
        if group_id < self.id and not self.first:
            first_node_data = self.find_first().decode().split('|')
            ip = first_node_data[0]
            port = int(first_node_data[1])
            first_node = NodeReference(ip, port)
            return first_node.list_group_agenda(group_id)
        else:
            return self._list_group_agenda(group_id)
    def _list_group_agenda(self, group_id: int) -> str:
        if (group_id < self.id) or (group_id > self.id and self.leader):
            agenda = self.db.list_group_agenda(group_id)
            return "\n".join(agenda)
        else:
            closest_node = self._closest_preceding_node(group_id)
            return closest_node.list_group_agenda(group_id)
#endregion


if __name__ == "__main__":
    server = ChordNode()