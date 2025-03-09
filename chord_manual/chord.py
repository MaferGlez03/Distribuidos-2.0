# region imports
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
import ssl
# endregion

# region constants
TCP_PORT = 8000  # puerto de escucha del socket TCP
UDP_PORT = 8888  # puerto de escucha del socket UDP
# Definición de operaciones Chord
GET_FIRST = 'get_first'
JOIN = 'join'
CONFIRM_JOIN = 'conf_join'
FIX_FINGER = 'fix_fing'
FIND_FIRST = 'fnd_first'
FIND_FIRST_TOTAL = 'fnd_first_total'
FIND_LEADER_TOTAL = 'fnd_leader_total'
REQUEST_DATA = 'req_data'
CHECK_PREDECESSOR = 'check_pred'
NOTIFY = 'notf'
UPDATE_PREDECESSOR = 'upt_pred'
UPDATE_FINGER = 'upd_fin'
UPDATE_SUCC = 'upd_suc'
UPDATE_PRED = 'upd_pred'
UPDATE_LEADER = 'upd_leader'
UPDATE_FIRST = 'upd_first'
UPDATE_FIRST_TOTAL = 'upd_first_total'
UPDATE_LEADER_TOTAL = 'upd_leader_total'
UPDATE_REPLI_LIST = 'upd_rep_list'
DATA_PRED = 'dat_prd'
FALL_SUCC = 'fal_suc'
LIST_SUCC = 'list_succ'
UPDATE_SUCC_LIST = 'upd_succ_list'
FALL_PRED = 'fal_suc'
LIST_PRED = 'list_pred'
UPDATE_PRED_LIST = 'upd_pred_list'

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
CREATE_INDIVIDUAL_EVENT = 'create_individual_event'
CONFIRM_EVENT = 'confirm_event'
CANCEL_EVENT = 'cancel_event'
LIST_EVENTS = 'list_events'
LIST_EVENTS_PENDING = 'list_events_pending'
LIST_CONTACTS = 'list_contacts'
REMOVE_CONTACT = 'remove_contact'
LIST_MEMBER = 'list_member'

BROADCAST_ID = 'broad_id'
BROADCAST_IP = '255.255.255.255'
# endregion


class NodeReference:
    def __init__(self, ip: int, port: int, set: bool = False):
        self.id = ip if set else self.set_id(str(ip))
        self.ip = None if set else ip
        self.port = port

    # Hashear la data
    def set_id(self, data: str) -> int:
        """
        Hashea una cadena usando SHA-1 y devuelve un entero.
        """
        # print("HASHING...")
        ret = int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 8)
        # print("data: ", data, "return: ", ret)
        return ret

    def send_data_tcp(self, op, data):
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False  # Desactivar verificación del hostname
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((self.ip, self.port)) as s:
                with context.wrap_socket(s, server_hostname=self.ip) as secure_sock:
                    secure_sock.sendall(f'{op}|{data}'.encode('utf-8'))
                    return secure_sock.recv(1024)  # Recibir respuesta
        except Exception as e:
            print(f"❌ Error en send_data_tcp: {e}")
            return False


class ChordNode:
    def __init__(self):
        self.ip = self.get_ip()
        self.id = self.generate_id()
        self.tcp_port = TCP_PORT
        self.udp_port = UDP_PORT
        self.predecessor = NodeReference(self.ip, self.tcp_port)
        self.successor = NodeReference(self.ip, self.tcp_port)
        self.ip_table = {}  # IPs table: {ID: {IP, port}}
        # Finger table: {ID: Owner}
        self.finger_table = self.create_finger_table()
        self.leader = False
        self.first = False
        self.repli_pred = ''  # Lista de nodos caidos que son mi responsabilidad
        self.repli_pred_pred = ''
        self.actual_first_id = self.id
        self.actual_leader_id = self.id
        self.first_node = NodeReference(self.ip, self.tcp_port)

        self.handler_data = HandleData(self.id)
        # Cola de actualizaciones de finger table
        self.finger_update_queue = queue.Queue()
        # Cola de actualizaciones de finger table cuando se cae un nodo
        self.finger_update_fall_queue = queue.Queue()

        self.db = Database()

        threading.Thread(target=self.start_tcp_server).start()
        threading.Thread(target=self.start_broadcast).start()
        threading.Thread(target=self.check_predecessor).start()
        threading.Thread(target=self.handle_finger_table).start()
        threading.Thread(target=self.handle_finger_table_update).start()

        self.join()

    def register(self, id: int, name: str, email: str, password: str) -> str:
        print(f"register {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a registrar a { id } yo con {self.id}")
                return self._register(id, name, email, password)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REGISTER, f"{id}|{name}|{email}|{password}")

        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._register(id, name, email, password)
            else:
                # Reenviar al "first"
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REGISTER, f"{id}|{name}|{email}|{password}")
        else:
            # Registrar localmente
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(REGISTER, f"{id}|{name}|{email}|{password}")
# region DB

    def _register(self, id: int, name: str, email: str, password: str) -> str:

        success = self.db.register_user(name, email, password)
        print(success)
        return (f"User {name} registered") if success else (f"Failed to register user {name}")

    def login_user(self, id: int, name: str, password: str) -> str:
        if id > self.actual_leader_id:
            if self.first:
                return self._login_user(id, name, password)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LOGIN, f"{id}|{name}|{password}")

        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._login_user(id, name, password)
            else:
                # Reenviar al "first"
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LOGIN, f"{id}|{name}|{password}")
        else:
            # Registrar localmente
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LOGIN, f"{id}|{name}|{password}")

    def _login_user(self, id: int, name: str, password: str) -> str:

        success = self.db.login_user(name, password)
        print(success)
        return ("User logged", success[1]) if success else ("Failed to log user in", success[1])

    def create_event(self, event_id: int, name: str, date: str, privacy: str, group_id=None) -> str:
        if id > self.actual_leader_id:
            if self.first:
                return self._create_event(event_id, name, date, privacy, group_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_EVENT, f'{event_id}|{name}|{date}|{privacy}|{group_id}')

        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._create_event(event_id, name, date, privacy, group_id)
            else:
                # Reenviar al "first"
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_EVENT, f'{event_id}|{name}|{date}|{privacy}|{group_id}')
        else:
            # Registrar localmente
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(CREATE_EVENT, f'{event_id}|{name}|{date}|{privacy}|{group_id}')

    def _create_event(self, event_id: int, name: str, date: str, privacy: str, group_id=None) -> str:

        success = self.db.create_event(
            name, date, event_id, privacy, group_id)
        print(success)
        return f"Event created: {name}" if success else f"Failed to create event {name}"

    def create_group_event(self, event_id: int, name: str, date: str, group_id=None) -> str:
        print(f"register {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a registrar a { id } yo con {self.id}")
                return self._create_group_event(event_id, name, date, group_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_GROUP_EVENT, f'{event_id}|{name}|{date}|{group_id}')

        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._create_group_event(event_id, name, date, group_id)
            else:
                # Reenviar al "first"
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_GROUP_EVENT, f'{event_id}|{name}|{date}|{group_id}')
        else:
            # Registrar localmente
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(CREATE_GROUP_EVENT, f'{event_id}|{name}|{date}|{group_id}')

    def _create_group_event(self, event_id: int, name: str, date: str, group_id=None) -> str:

        success = self.db.create_group_event(
            name, date, event_id, group_id)
        print(success)
        return f"Event created: {name}" if success else f"Failed to create event {name}"

    def create_individual_event(self, event_id: int, name: str, date: str, group_id=None) -> str:
        print(f"register {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a registrar a { id } yo con {self.id}")
                return self._create_individual_event(event_id, name, date, group_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_INDIVIDUAL_EVENT, f'{event_id}|{name}|{date}|{group_id}')

        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._create_individual_event(event_id, name, date, group_id)
            else:
                # Reenviar al "first"
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_INDIVIDUAL_EVENT, f'{event_id}|{name}|{date}|{group_id}')
        else:
            # Registrar localmente
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(CREATE_INDIVIDUAL_EVENT, f'{event_id}|{name}|{date}|{group_id}')

    def _create_individual_event(self, event_id: int, name: str, date: str, group_id=None) -> str:

        success = self.db.create_individual_event(
            name, date, event_id, group_id)
        return f"Event created: {name}" if success else f"Failed to create event {name}"

    def register(self, id: int, name: str, email: str, password: str) -> str:
        print(f"register {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a registrar a { id } yo con {self.id}")
                return self._register(id, name, email, password)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REGISTER, f"{id}|{name}|{email}|{password}")

        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._register(id, name, email, password)
            else:
                # Reenviar al "first"
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REGISTER, f"{id}|{name}|{email}|{password}")
        else:
            # Registrar localmente
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(REGISTER, f"{id}|{name}|{email}|{password}")

    def confirm_event(self, id: int, user_id: int, event_id: int) -> str:
        print(f"confirm_event {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a confirmar evento {event_id} yo con {self.id}")
                return self._confirm_event(user_id, event_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CONFIRM_EVENT, f"{id}|{user_id}|{event_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._confirm_event(user_id, event_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CONFIRM_EVENT, f"{id}|{user_id}|{event_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(CONFIRM_EVENT, f"{id}|{user_id}|{event_id}")

    def cancel_event(self, id: int, user_id: int, event_id: int) -> str:
        print(f"cancel_event {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a cancelar evento {event_id} yo con {self.id}")
                return self._cancel_event(user_id, event_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CANCEL_EVENT, f"{id}|{user_id}|{event_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._cancel_event(user_id, event_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CANCEL_EVENT, f"{id}|{user_id}|{event_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(CANCEL_EVENT, f"{id}|{user_id}|{event_id}")

    def list_events(self, id: int, user_id: int) -> str:
        print(f"list_events {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a listar eventos de {user_id} yo con {self.id}")
                return self._list_events(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_EVENTS, f"{id}|{user_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._list_events(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_EVENTS, f"{id}|{user_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LIST_EVENTS, f"{id}|{user_id}")

    def list_events_pending(self, id: int, user_id: int) -> str:
        print(f"list_events_pending {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(
                    f"voy a listar eventos pendientes de {user_id} yo con {self.id}")
                return self._list_events_pending(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_EVENTS_PENDING, f"{id}|{user_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._list_events_pending(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_EVENTS_PENDING, f"{id}|{user_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LIST_EVENTS_PENDING, f"{id}|{user_id}")

    def add_contact(self, id: int, user_id: int, contact_name: str, owner_id: int) -> str:
        print(f"add_contact {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a añadir contacto {contact_name} yo con {self.id}")
                return self._add_contact(user_id, contact_name, owner_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(ADD_CONTACT, f"{id}|{user_id}|{contact_name}|{owner_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._add_contact(user_id, contact_name, owner_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(ADD_CONTACT, f"{id}|{user_id}|{contact_name}|{owner_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(ADD_CONTACT, f"{id}|{user_id}|{contact_name}|{owner_id}")

    def remove_contact(self, id: int, user_id: int, contact_id: int) -> str:
        print(f"remove_contact {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a eliminar contacto {contact_id} yo con {self.id}")
                return self._remove_contact(user_id, contact_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REMOVE_CONTACT, f"{id}|{user_id}|{contact_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._remove_contact(user_id, contact_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REMOVE_CONTACT, f"{id}|{user_id}|{contact_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(REMOVE_CONTACT, f"{id}|{user_id}|{contact_id}")

    def list_contacts(self, id: int, user_id: int) -> str:
        print(f"list_contacts {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a listar contactos de {user_id} yo con {self.id}")
                return self._list_contacts(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_CONTACTS, f"{id}|{user_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._list_contacts(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_CONTACTS, f"{id}|{user_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LIST_CONTACTS, f"{id}|{user_id}")

    def create_group(self, id: int, owner_id: int, name: str) -> str:
        print(f"create_group {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a crear grupo {name} yo con {self.id}")
                return self._create_group(owner_id, name)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_GROUP, f"{id}|{owner_id}|{name}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._create_group(owner_id, name)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(CREATE_GROUP, f"{id}|{owner_id}|{name}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(CREATE_GROUP, f"{id}|{owner_id}|{name}")

    def delete_group(self, id: int, owner_id: int, name: str) -> str:
        print(f"delete_group {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a eliminar grupo {name} yo con {self.id}")
                return self._delete_group(owner_id, name)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(DELETE_GROUP, f"{id}|{owner_id}|{name}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._delete_group(owner_id, name)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(DELETE_GROUP, f"{id}|{owner_id}|{name}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(DELETE_GROUP, f"{id}|{owner_id}|{name}")

    def leave_group(self, id: int, name: str, owner_id: int) -> str:
        print(f"leave_group {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a abandonar grupo {name} yo con {self.id}")
                return self._leave_group(owner_id, name)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LEAVE_GROUP, f"{id}|{name}|{owner_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._leave_group(owner_id, name)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LEAVE_GROUP, f"{id}|{name}|{owner_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LEAVE_GROUP, f"{id}|{name}|{owner_id}")

    def add_member_to_group(self, id: int, group_id: int, user_id: int, role: str) -> str:
        print(f"add_member_to_group {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(
                    f"voy a añadir miembro {user_id} al grupo {group_id} yo con {self.id}")
                return self._add_member_to_group(group_id, user_id, role)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(ADD_MEMBER, f"{id}|{group_id}|{user_id}|{role}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._add_member_to_group(group_id, user_id, role)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(ADD_MEMBER, f"{id}|{group_id}|{user_id}|{role}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(ADD_MEMBER, f"{id}|{group_id}|{user_id}|{role}")

    def remove_member_from_group(self, id: int, group_id: int, user_id: int) -> str:
        print(f"remove_member_from_group {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(
                    f"voy a eliminar miembro {user_id} del grupo {group_id} yo con {self.id}")
                return self._remove_member_from_group(group_id, user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REMOVE_MEMBER, f"{id}|{group_id}|{user_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._remove_member_from_group(group_id, user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(REMOVE_MEMBER, f"{id}|{group_id}|{user_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(REMOVE_MEMBER, f"{id}|{group_id}|{user_id}")

    def list_group(self, id: int, user_id: int) -> str:
        print(f"list_group {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(f"voy a listar grupos de {user_id} yo con {self.id}")
                return self._list_group(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_GROUPS, f"{id}|{user_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._list_group(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_GROUPS, f"{id}|{user_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LIST_GROUPS, f"{id}|{user_id}")

    def list_member(self, id: int, user_id: int, group_id: int) -> str:
        print(f"list_member {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(
                    f"voy a listar miembros del grupo {group_id} yo con {self.id}")
                return self._list_member(user_id, group_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_MEMBER, f"{id}|{user_id}|{group_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._list_member(user_id, group_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_MEMBER, f"{id}|{user_id}|{group_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LIST_MEMBER, f"{id}|{user_id}|{group_id}")

    def list_personal_agenda(self, id: int, user_id: int) -> str:
        print(f"list_personal_agenda {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(
                    f"voy a listar agenda personal de {user_id} yo con {self.id}")
                return self._list_personal_agenda(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_PERSONAL_AGENDA, f"{id}|{user_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._list_personal_agenda(user_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_PERSONAL_AGENDA, f"{id}|{user_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LIST_PERSONAL_AGENDA, f"{id}|{user_id}")

    def list_group_agenda(self, id: int, group_id: int) -> str:
        print(f"list_group_agenda {id} {self.id}")
        if id > self.actual_leader_id:
            if self.first:
                print(
                    f"voy a listar agenda del grupo {group_id} yo con {self.id}")
                return self._list_group_agenda(group_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_GROUP_AGENDA, f"{id}|{group_id}")
        elif id < self.id:
            if id > self.predecessor.id or self.first:
                return self._list_group_agenda(group_id)
            else:
                self.find_first()
                time.sleep(3)
                return self.first_node.send_data_tcp(LIST_GROUP_AGENDA, f"{id}|{group_id}")
        else:
            print("Voy a la finger table")
            return self._closest_preceding_node(id).send_data_tcp(LIST_GROUP_AGENDA, f"{id}|{group_id}")

    # Funciones privadas (_)

    def _confirm_event(self, user_id: int, event_id: int) -> str:
        success = self.db.confirm_event(event_id)
        return "Event confirmed" if success else "Failed to confirm event"

    def _cancel_event(self, user_id: int, event_id: int) -> str:
        success = self.db.cancel_event(event_id)
        return "Event canceled" if success else "Failed to cancel event"

    def _list_events(self, user_id: int) -> str:
        events = self.db.list_events(user_id)
        return "\n".join([str(event) for event in events])

    def _list_events_pending(self, user_id: int) -> str:
        events = self.db.list_events_pending(user_id)
        return "\n".join([str(event) for event in events])

    def _add_contact(self, user_id: int, contact_name: str, owner_id: int) -> str:
        success = self.db.add_contact(user_id, contact_name, owner_id)
        return "Contact added" if success else "Failed to add contact"

    def _remove_contact(self, user_id: int, contact_id: int) -> str:
        success = self.db.delete_contact(contact_id)
        return "Contact removed" if success else "Failed to remove contact"

    def _list_contacts(self, user_id: int) -> str:
        contacts = self.db.list_contacts(user_id)
        return "\n".join(contacts)

    def _create_group(self, owner_id: int, name: str) -> str:
        success = self.db.create_group(name, owner_id)
        return "Group created" if success else "Failed to create group"

    def _delete_group(self, owner_id: int, name: str) -> str:
        success = self.db.delete_group(name)
        return "Group deleted" if success else "Failed to delete group"

    def _leave_group(self, owner_id: int, name: str) -> str:
        success = self.db.leave_group(name)
        return "Group leaved" if success else "Failed to leave group"

    def _add_member_to_group(self, group_id: int, user_id: int, role: str) -> str:
        success = self.db.add_member_to_group(group_id, user_id, role)
        return "Member added" if success else "Failed to add member"

    def _remove_member_from_group(self, group_id: int, user_id: int) -> str:
        success = self.db.remove_member_from_group(group_id, user_id)
        return "Member removed" if success else "Failed to remove member"

    def _list_group(self, user_id: int) -> str:
        agenda = self.db.list_groups(user_id)
        groups_list = [{'id': g[0], 'name': g[1]} for g in agenda]
        return "\n".join(groups_list)

    def _list_member(self, user_id: int, group_id: int) -> str:
        agenda = self.db.list_members(group_id)
        return "\n".join(agenda)

    def _list_personal_agenda(self, user_id: int) -> str:
        agenda = self.db.list_personal_agenda(user_id)
        return "\n".join(agenda)

    def _list_group_agenda(self, group_id: int) -> str:
        agenda = self.db.list_group_agenda(group_id)
        return "\n".join(agenda)
# endregion
# region CHORD

    def start_tcp_server(self):
        """Iniciar el servidor TCP con SSL."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            certfile="/app/certificate.pem", keyfile="/app/private_key.pem")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.tcp_port))
            s.listen()

            print(f'🔒 Servidor SSL TCP en ({self.ip}, {self.tcp_port})')

            with context.wrap_socket(s, server_side=True) as secure_socket:
                while True:
                    conn, addr = secure_socket.accept()
                    print(f"🔵 Conexión aceptada desde {addr}")
                    # Envía una respuesta al cliente
                    #conn.sendall(b"Servidor activo\n")
                    client = threading.Thread(
                    target=self._handle_client_tcp, args=(conn, addr))
                    client.start()

    def _handle_client_tcp(self, conn: socket.socket, addr: tuple):
        data = conn.recv(1024).decode().split('|')  # operation | id | port
        option = data[0]
        if option == '':
            return
        id = data[1]
        response = f'ok'
        # print("ANALIZANDO MENSAJE EN TCP: ", option)

        if option == FIX_FINGER:
            self.finger_update_queue.put((id, TCP_PORT))
            return

        elif option == REPLICATE:
            real_data = conn.recv(1024).decode().split('$$')
            for datas in real_data[1:]:
                self.handler_data.create(datas)

        elif option == LOGIN:
            # Iniciar sesión
            id = data[1]
            email = data[2]
            password = data[3]
            response = self.login_user(id, email, password)

        elif option == CREATE_EVENT:
            # Crear un evento
            event_id = int(data[1])
            name = data[2]
            date = data[3]
            privacy = data[4]
            group_id = int(data[5]) if len(data) > 5 else None
            response = self.create_event(
                event_id, name, date, privacy, group_id)
        elif option == CREATE_GROUP_EVENT:
            # Crear un evento
            event_id = int(data[1])
            name = data[2]
            date = data[3]
            group_id = int(data[4]) if len(data) > 4 else None
            response = self.create_group_event(
                event_id, name, date, group_id)
        elif option == CREATE_INDIVIDUAL_EVENT:
            # Crear un evento
            event_id = int(data[1])
            name = data[2]
            date = data[3]
            group_id = int(data[4]) if len(data) > 4 else None
            response = self.create_individual_event(
                event_id, name, date, group_id)
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
            id = int(data[1])
            group_id = int(data[2])
            user_id = int(data[3])
            response = self.add_member_to_group(id, group_id, user_id)
        elif option == REMOVE_MEMBER:
            # Agregar un miembro a un grupo
            id = int(data[1])
            group_id = int(data[2])
            user_id = int(data[3])
            response = self.remove_member_from_group(id, group_id, user_id)

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
            response = self.login_user(id, email, password)
        elif option == CREATE_EVENT:
            # Crear un evento
            event_id = int(data[1])
            name = data[2]
            date = data[3]
            privacy = data[4]
            group_id = int(data[5]) if len(data) > 5 else None
            response = self.create_event(
                event_id, name, date, privacy, group_id)
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
            response = self.create_individual_event(
                event_id, name, date, group_id)
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
            id = int(data[1])
            group_id = int(data[2])
            user_id = int(data[3])
            response = self.add_member_to_group(id, group_id, user_id)
        elif option == REMOVE_MEMBER:
            # Agregar un miembro a un grupo
            id = int(data[1])
            group_id = int(data[2])
            user_id = int(data[3])
            response = self.remove_member_from_group(id, group_id, user_id)
        elif option == LIST_GROUPS:
            # Listar grupos de un usuario
            user_id = int(data[1])
            response = self.list_group(user_id)
        elif option == LIST_MEMBER:
            # Listar grupos de un usuario
            user_id = int(data[2])
            group_id = int(data[1])
            response = self.list_member(user_id, group_id)
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
            response = ""
            #self.handler_data.data(False, id)

        elif option == CHECK_PREDECESSOR:
            # !AQUI EL OBJETIVO ES OBTENE LA DATA DE MI PREDECESOR
            response = (f'0|' + self.predecessor.ip)
            #self.handler_data.data(False)
            # si somos al menos 3 nodos, le mando a mi sucesor la data de mi predecesor
            if self.predecessor.id != self.successor.id:
                self.successor.send_data_tcp(DATA_PRED, self.repli_pred)

        elif option == DATA_PRED:
            data_ = data[1]
            # !AQUI TAL VEZ HAY Q CAMBIAR LA LOGICA POR LA FORMA DE REPLICAR
            self.repli_pred_pred = data_

        elif option == FALL_SUCC:
            print("FALL SUCC FALL SUCC FALL SUCC FALL SUCC FALL SUCC")
            ip = data[1]
            port = int(data[2])
            self.successor = NodeReference(ip, port)
            response = f'ok'
            # pido data a mi sucesor al actualizar mi posicion
            # !ESTO es lo del balanceo de carga
            # self.request_succ_data(succ=True)
            # si se cayo mi sucesor, le digo a su sucesor que soy su  nuevo predecesor
            self.successor.send_data_tcp(
                UPDATE_PREDECESSOR, f'{self.ip}|{self.tcp_port}')

        elif option == UPDATE_PREDECESSOR:
            ip = data[1]
            port = int(data[2])
            self.predecessor = NodeReference(ip, port)

        elif option == SUCC_PROPAGATION:
            propagation = int(data[2]) - 1
            self.pred_queue.replace_at(id, propagation)

            self.successor.send_data_tcp(option, f'{self.id}|{PROPAGATION}')

            # Enviar al siguiente si todavia el valor de propagacion > 0
            if propagation > 0:
                self.successor.send_data_tcp(option, f'{id}|{propagation}')

        elif option == PRED_PROPAGATION:
            propagation = int(data[2]) - 1
            self.succ_queue.replace_at(id, propagation)

            self.predecessor.send_data_tcp(option, f'{self.id}|{PROPAGATION}')

            # Enviar al siguiente si todavia el valor de propagacion > 0
            if propagation > 0:
                self.predecessor.send_data_tcp(option, f'{id}|{propagation}')

        elif option == LIST_SUCC:
            st1 = ''
            for e in self.succ_list:
                st1 += f'{e.ip}|'
            response = st1[:-1]

        elif option == UPDATE_SUCC_LIST:
            # Para cuando se cae un nodo
            print(f"DATA-SUCC$: {data}")
            if data[1] == '$':
                self.get_succ_list()
            # Para cuando se sigue a partir de un sucesor
            self.get_succ_list(data[1:])

        elif option == LIST_PRED:
            st1 = ''
            for e in self.pred_list:
                st1 += f'{e.ip}|'
            response = st1[1:]

        elif option == UPDATE_PRED_LIST:
            # Para cuando se cae un nodo
            print(f"DATA-PRED$: {data}")
            if data[1] == '$':
                self.get_pred_list()
            # Para cuando se sigue a partir de un predecesor
            self.get_pred_list(data[1:])

        elif option == UPDATE_REPLI_LIST:
            print(f'REPLICANDO {id} EN {self.id}')
            self.repli_pred_list.append(id)
            return f'ok'

        else:
            # Operación no reconocida
            response = "Invalid operation"

    # Enviar respuesta al cliente
        conn.sendall(response.encode())
        conn.close()

        # print("conn, addr, data", conn, addr, data)
        # print("option, info, ip, port", option, id)

    def set_first_(self) -> bytes:
        while (True):
            self.first = True if self.predecessor.id == self.id or self.predecessor.id > self.id else False

    def set_leader_(self):
        while (True):
            self.leader = True if self.predecessor.id == self.id or self.successor.id < self.id else False

    def check_predecessor(self):
        print(
            f"el id de mi predecesor es {self.predecessor.id} y el mio {self.id}")
        while True:
            if self.predecessor.id != self.id:
                print(
                    f"PREDECESOR: {self.predecessor.id}   YO: {self.id}    SUCESOR: {self.successor.id}")
                print("Somos diferentes")

                try:
                    print("Voy a tratar de conectar")
                    with socket.create_connection((self.predecessor.ip, self.predecessor.port)) as s:
                        # Configurar SSL para la conexión con el predecesor
                        context = ssl.create_default_context(
                            ssl.Purpose.SERVER_AUTH)
                        context.check_hostname = False  # Desactivar verificación del hostname
                        context.verify_mode = ssl.CERT_NONE

                        with context.wrap_socket(s, server_hostname=self.predecessor.ip) as secure_sock:
                            # Configuramos el socket para lanzar un error si no recibe respuesta en 10 segundos
                            secure_sock.settimeout(10)
                            print("conecto")

                            op = CHECK_PREDECESSOR
                            data = f"0|0"
                            # Chequeamos que no se ha caído el predecesor
                            secure_sock.sendall(f'{op}|{data}'.encode('utf-8'))
                            # Guardamos la info recibida
                            self.repli_pred = secure_sock.recv(1024).decode()
                            # Guardamos el id del predecesor de nuestro predecesor
                            ip_pred_pred = self.repli_pred.split('|')[-1]
                except:
                    print(
                        f"El servidor {self.predecessor.ip} se ha desconectado")
                    # self.update_repli_list(self.predecessor.id)
                    # replicar la info del predecesor que se cayó
                    #self.handler_data.create(self.repli_pred)
                    # actualizar el first y el leader
                    if self.first:
                        self.send_data_broadcast(
                            UPDATE_LEADER, f"{self.generate_id_(ip_pred_pred)}|{TCP_PORT}|{self.predecessor.id}")
                        time.sleep(2)
                    elif self.actual_first_id == self.predecessor.id:
                        self.send_data_broadcast(
                            UPDATE_FIRST, f"{self.id}|{TCP_PORT}|{self.predecessor.id}")
                        time.sleep(2)
                    # actualizar la finger table
                    self.send_data_broadcast(
                        UPDATE_FINGER, f"{self.predecessor.id}|{self.ip}|{TCP_PORT}")
                    if self.predecessor.id != self.successor.id:  # somos al menos 3
                        try:
                            # tratamos de conectarnos con el predecesor de nuestro predecesor para comunicarle que se cayo su sucesor
                            # seguimos el mismo proceso
                            with socket.create_connection((ip_pred_pred, TCP_PORT)) as s:
                                # Configurar SSL para la conexión con el predecesor del predecesor
                                context = ssl.create_default_context(
                                    ssl.Purpose.SERVER_AUTH)
                                context.check_hostname = False  # Desactivar verificación del hostname
                                context.verify_mode = ssl.CERT_NONE

                                with context.wrap_socket(s, server_hostname=ip_pred_pred) as secure_sock:
                                    # Configurar timeout
                                    secure_sock.settimeout(10)
                                    secure_sock.sendall(
                                        f'{FALL_SUCC}|{self.ip}|{self.tcp_port}'.encode('utf-8'))
                                    # Esperar respuesta
                                    secure_sock.recv(1024).decode()
                                # print(self.predecessor.id)
                                # print(self.successor.id)
                            # Iniciar actualizaciones de listas de sucesores a partir del predecesor del predecesor
                            # time.sleep(5)
                            # threading.Thread(target=NodeReference(ip_pred_pred, self.tcp_port).send_data_tcp, args=(UPDATE_SUCC_LIST, f'$')).start()
                            # time.sleep(5)
                            # threading.Thread(target=NodeReference(self.ip, self.tcp_port).send_data_tcp, args=(UPDATE_PRED_LIST, f'$')).start()
                            # self.update_repli_list(self.predecessor.id)
                        except:
                            print(
                                f"El servidor {ip_pred_pred} se ha desconectado tambien")
                            # self.update_repli_list(self.generate_id(ip_pred_pred))
                            # replicar data
                            #self.handler_data.create(self.repli_pred_pred)
                            if ip_pred_pred != self.successor.ip:
                                if self.generate_id_(ip_pred_pred) == self.actual_first_id:
                                    self.send_data_broadcast(
                                        UPDATE_FIRST, f"{self.id}|{TCP_PORT}|{self.predecessor.id}")
                                time.sleep(2)
                                self.send_data_broadcast(
                                    NOTIFY, f"{self.generate_id_(ip_pred_pred)}")
                                print(f"Solo eramos tres nodos me reinicio")
                                self.send_data_broadcast(
                                    UPDATE_FIRST, f"{self.id}|{TCP_PORT}|{self.predecessor.id}")
                                self.send_data_broadcast(
                                    UPDATE_LEADER, f"{self.id}|{TCP_PORT}|{self.predecessor.id}")
                                self.predecessor = NodeReference(
                                    self.ip, self.tcp_port)
                                self.successor = NodeReference(
                                    self.ip, self.tcp_port)
                                self.finger_table = self.create_finger_table()

                    else:
                        print(f"Solo eramos dos nodos me reinicio")
                        self.send_data_broadcast(
                            UPDATE_FIRST, f"{self.id}|{TCP_PORT}|{self.predecessor.id}")
                        self.send_data_broadcast(
                            UPDATE_LEADER, f"{self.id}|{TCP_PORT}|{self.predecessor.id}")
                        self.predecessor = NodeReference(
                            self.ip, self.tcp_port)
                        self.successor = NodeReference(self.ip, self.tcp_port)
                        self.finger_table = self.create_finger_table()

                # self.replicate()
                time.sleep(5)

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
                # print(f"Mensaje enviado por broadcast. Operation: {op} Data: {data}")
        except Exception as e:
            print(
                f"Error al enviar mensaje por broadcast. Operation: {op} Data: {data} Error: {e}")

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
                # "" significa que escucha en todas las interfaces
                s.bind(("", self.udp_port))

                print(
                    f"[+] Escuchando broadcast en el puerto {self.udp_port}...")

                while True:
                    time.sleep(1)
                    # Recibir datos
                    datos, direccion = s.recvfrom(1024)
                    mensaje = datos.decode('utf-8')
                    if mensaje == "DISCOVER":
                        response = f"{self.ip}:{self.tcp_port}".encode()
                        s.sendto(response, direccion)
                        print(f"🔹 Respondió a DISCOVER de {direccion}")
                    else:
                        thread = threading.Thread(
                            target=self.handle_broadcast, args=(mensaje, direccion))
                        thread.start()
        except Exception as e:
            print(f"[!] Error al recibir broadcast: {e}")

    def handle_broadcast(self, mensaje, direccion):
        # Maneja el mensaje entrante
        # operation | id | port | (other_id) | (other_port)
        data = mensaje.split('|')
        option = data[0]
        if option == '':
            return
        if data[1] != None:
            ip = data[1]
        print("ANALIZANDO MENSAJE: ", option)
        address = direccion[0]

        if option == JOIN:
            port = int(data[2])
            id = self.generate_id_(ip)
            # No hacer nada si recibo la operacion de mi mismo
            if self.id == id:
                time.sleep(2)

            # Me estoy uniendo a una red donde solo hay un nodo
            elif self.id == self.successor.id and self.id == self.predecessor.id:
                print(
                    f"Me estoy uniendo a una red donde solo hay un nodo({self.id})")
                # Actualiza mi self.successor a id
                op = UPDATE_SUCC
                data = f'{self.id}|{self.tcp_port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza mi self.predecessor a id
                op = UPDATE_PREDECESSOR
                data = f'{self.id}|{self.tcp_port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.sucesor a self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.ip}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.predecesor a self.id
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.ip}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualizo first y leader
                if self.id > id:
                    self.set_leader(self.id, self.tcp_port, id, port)
                    self.set_first(id, port, self.id, self.tcp_port)
                elif self.id < id:
                    self.set_first(self.id, self.tcp_port, id, port)
                    self.set_leader(id, port, self.id, self.tcp_port)

                print("self.ip, self.predecessor.ip, self.successor.ip: ",
                      self.ip, self.predecessor.ip, self.successor.ip)
        # Hay 2 nodos o mas
            # Esta entre yo y mi predecesor
            elif self.id > id and self.predecessor.id < id:
                print(
                    f"Esta entre yo({self.id}) y mi predecesor({self.predecessor.id})")
                # Actualiza mi sucesor por el nodo entrante
                op = UPDATE_SUCC
                data = f'{self.predecessor.id}|{self.predecessor.port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza mi predecesor por el nodo entrante
                op = UPDATE_PREDECESSOR
                data = f'{self.id}|{self.tcp_port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.sucesor a self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.ip}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza id.predecesor a self.id
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.predecessor.ip}|{self.predecessor.port}'
                self.send_data_broadcast(op, data)
                print("self.ip, self.predecessor.ip, self.successor.ip: ",
                      self.ip, self.predecessor.ip, self.successor.ip)

            # Es menor que yo y soy el first
            elif self.id > id and self.first:
                print(
                    f"Es menor que yo({self.id}) y soy el first({self.first})")
                # Actualiza el predecesor del nodo entrante por self.predecesor
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.predecessor.ip}|{self.predecessor.port}'
                self.send_data_broadcast(op, data)

                # Actualiza el sucesor del nodo entrante por self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.ip}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza mi predecesor por el nodo entrante
                op = UPDATE_PREDECESSOR
                data = f'{self.id}|{self.tcp_port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza el sucesor de mi predecesor por el nodo entrante
                op = UPDATE_SUCC
                data = f'{self.predecessor.id}|{self.predecessor.port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualizo first
                self.set_first(id, port, self.id, self.tcp_port)

                print("self.ip, self.predecessor.ip, self.successor.ip: ",
                      self.ip, self.predecessor.ip, self.successor.ip)

            # Es mayor que yo y soy el leader
            elif self.id < id and self.leader:
                print(
                    f"Es mayor que yo({self.id}) y soy el leader({self.leader})")
                # Actualiza el sucesor del nodo entrante por mi sucesor
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.successor.ip}|{self.successor.port}'
                self.send_data_broadcast(op, data)

                # Actualiza el predecesor del nodo entrante por mi
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.ip}|{self.tcp_port}'
                self.send_data_broadcast(op, data)

                # Actualiza mi sucesor por el nodo entrante
                op = UPDATE_SUCC
                data = f'{self.id}|{self.tcp_port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualiza el predecesor de mi sucesor por el nodo entrante
                op = UPDATE_PREDECESSOR
                data = f'{self.successor.id}|{self.successor.port}|{ip}|{port}'
                self.send_data_broadcast(op, data)

                # Actualizo leader
                self.set_leader(id, port, self.id, self.tcp_port)

                print("self.ip, self.predecessor.ip, self.successor.ip: ",
                      self.ip, self.predecessor.ip, self.successor.ip)

        elif option == FIND_FIRST:
            if self.first == True:
                print("Estoy buscando el first y ")
                self.first_node = NodeReference(address, TCP_PORT)

        elif option == UPDATE_SUCC:
            id = int(data[1])
            new_ip = data[3]
            new_id = self.generate_id_(new_ip)
            new_port = int(data[4])
            print("CHECK successor: ", self.id, id,
                  self.id == id, new_id, new_port)
            if self.id == id:
                print("UPDATE_SUCC")
                self.successor = NodeReference(new_ip, new_port)

        elif option == UPDATE_PREDECESSOR:
            id = int(data[1])
            new_ip = data[3]
            new_id = self.generate_id_(new_ip)
            new_port = int(data[4])
            print("CHECK PREDECESSOR: ", self.id, id,
                  self.id == id, new_id, new_port)
            if self.id == id:
                print("UPDATE_PREDECESSOR")
                self.predecessor = NodeReference(new_ip, new_port)

        elif option == FIX_FINGER:

            if address != self.ip:
                # el nodo que entra es mayor que yo, lo pongo en mi lista para actualizar mi finger teble.
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
            id = int(data[1])
            old_id = int(data[3])
            self.actual_first_id = id

            if self.id == id:
                print(f"CONFIRMADO: {id} es el nuevo first")
                self.first = True
            elif self.id == old_id:
                print(f"CONFIRMADO: {old_id} ya no es first")
                self.first = False

        elif option == UPDATE_LEADER:
            id = int(data[1])
            old_id = int(data[3])
            self.actual_leader_id = id

            if self.id == id:
                print(f"CONFIRMADO: {id} es el nuevo lider")
                self.leader = True
            elif self.id == old_id:
                print(f"CONFIRMADO: {old_id} ya no es lider")
                self.leader = False

        elif option == FIND_FIRST_TOTAL:
            if self.first:
                self.get_first(self.id, self.tcp_port)

        elif option == UPDATE_FIRST_TOTAL:
            id = int(data[1])
            self.actual_first_id = id

        elif option == FIND_LEADER_TOTAL:
            if self.leader:
                self.get_leader(self.id, self.tcp_port)

        elif option == UPDATE_LEADER_TOTAL:
            id = int(data[1])
            self.actual_leader_id = id

        elif option == UPDATE_FINGER:
            id = int(data[1])
            ip = data[2]
            port_ = data[3]
            # aqui port en realidad es un ip
            self.finger_update_fall_queue.put((id, ip, port_))

        elif option == NOTIFY:
            # print("NOTIFYNOTIFYNOTIFYNOTIFYNOTIFYNOTIFYNOTIFY")
            id = int(data[1])
            if address != self.ip:
                # si se cayo mi sucesor, me actualizo con quien lo notifico, le pido data si tiene y le comunico que se actualice conmigo
                if self.successor.id == id:
                    if self.actual_leader_id == id:
                        self.send_data_broadcast(
                            UPDATE_LEADER, f"{self.id}|{TCP_PORT}|{id}")
                        time.sleep(2)
                    #!self._request_data(succ=True)
                    self.successor = NodeReference(address, self.tcp_port)
                    self.successor.send_data_tcp(
                        UPDATE_PREDECESSOR, f'{self.ip}|{self.tcp_port}')
                    # si el nodo que me notifico tiene menor id que yo, que actualicen al nodo caido conmigo, pues soy el nuevo lider
                    # en caso contrario, que actualicen con el nodo notificante
                    self.send_data_broadcast(
                        UPDATE_FINGER, f"{id}|{address}|{TCP_PORT}")

    def join(self):
        op = JOIN
        data = f'{self.ip}|{self.tcp_port}'
        self.send_data_broadcast(op, data)
        time.sleep(5)
        self.request_first()
        self.request_leader()
        time.sleep(5)
        self.send_data_broadcast(FIX_FINGER, f'0|0')
        #data = self.successor.send_data_tcp(REQUEST_DATA, self.id).decode()
        #self.handler_data.create(data)
        #self.handler_data.data(True, self.predecessor.id)

    def create_finger_table(self):
        table = {}
        id = self.id
        for i in range(8):
            self.ip_table[id] = self.ip
            table[(id + 2**i) % 256] = NodeReference(self.ip, self.tcp_port)
        return table

    def handle_finger_table(self):
        """
        Hilo que maneja las actualizaciones de la tabla de fingers.
        """
        while True:
            try:
                ip, port = self.finger_update_queue.get()
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
                id, ip, port = self.finger_update_fall_queue.get()
                # print(node)

                self.fix_finger_table(NodeReference(ip, port), id)
                print("Finger table arreglada")

            finally:
                self.finger_update_fall_queue.task_done()
                self.print_finger_table()

    def fix_finger_table(self, node: NodeReference, id=None):
        """
        Corrige la tabla de fingers si un nodo deja de responder o cambia la red.
        """
        print("[!] Verificando y corrigiendo tabla de fingers...")
        for i in range(8):
            finger_id = (self.id + 2**i) % 256
            if id == None:
                # si el nodo nuevo es menor que el que se esta haciendo cargo
                # print(f"  Yo{self.id} Me actualizo con {node.id}")
                # print(f"fingerid: {finger_id}")
                # print(f" actual first: {self.actual_first_id}")
                if node.id < self.finger_table[finger_id].id:
                    # si me puedo hacer cargo
                    print(
                        f" nodo encargado del finger {finger_id} es {self.finger_table[finger_id].id} ")
                    if (finger_id) <= node.id:
                        self.finger_table[finger_id] = node
                        print(
                            f"[+] Finger {finger_id} actualizado a {node.id}")

                    elif self.actual_first_id == node.id and self.finger_table[finger_id].id < (finger_id):
                        self.finger_table[finger_id] = node
                        print(
                            f"[+] Finger {finger_id} actualizado a {node.id}")

                # si el nodo es mayor que el que se esta haciendo cargo, pero este se esta haciendo cargo de un dato con id mas grande.
                elif self.finger_table[finger_id].id < (finger_id) and finger_id <= node.id:
                    self.finger_table[finger_id] = node
                    print(f"[+] Finger {finger_id} actualizado a {node.id}")
            else:
                print("UPDATE DE CAIDA")
                if self.finger_table[finger_id].id == id:
                    self.finger_table[finger_id] = node

    def print_finger_table(self):
        print(
            f" Nodo: {self.id} FINGER TABLE. FIRST: {self.first}. LEADER: {self.leader}")
        print(
            f"PREDECESOR: {self.predecessor.id} YO: {self.id} SUCESOR: {self.successor.id}")
        print(
            f"ACTUAL FIRST: {self.actual_first_id} | ACTUAL LEADER: {self.actual_leader_id}")
        for i in range(8):
            finger_id = (self.id + 2**i) % 256
            print(
                f"id: {finger_id} |||| owner: {self.finger_table[finger_id].id} \n")

    def _closest_preceding_node(self, id) -> NodeReference:
        """Devuelve el nodo más cercano a un ID en la finger table."""
        for i in range(8):
            if (self.id + (2**i) % 256) > id:
                if self.finger_table[self.id + (2**(i-1)) % 256] >= id:
                    return self.finger_table[self.id + (2**(i-1)) % 256]
                else:
                    return self.finger_table[self.id + (2**(i)) % 256]
        return self.finger_table[self.id + (2**(i)) % 256]

    def find_first(self) -> bytes:
        """Buscar el primer nodo."""
        self.send_data_broadcast(FIND_FIRST, f'0|0')

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

    def request_leader(self):
        print("BUSCANDO LIDER")
        op = FIND_LEADER_TOTAL
        data = f'{0}|{0}'
        self.send_data_broadcast(op, data)

    def get_leader(self, id, port):
        print(f"LIDER ACTUAL: {id}")
        op = UPDATE_LEADER_TOTAL
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
                # Fallback a localhost
                ip_local = f'10.2.0.{random.randint(2, 10)}'
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

    def init_queue(self):
        q = FlexibleQueue()
        for _ in range(PROPAGATION):
            q.push_front(self.id)
        return q

    def get_successor_list(self, k):
        """
        Retorna una lista de hasta k sucesores del nodo actual en el anillo Chord.
        """
        successor_list = []
        current = self.successor  # Comenzamos con el sucesor inmediato

        while len(successor_list) < k and current.id != self.id:
            successor_list.append(current)

            # Intentamos pedir la lista de sucesores al siguiente nodo
            try:
                remote_successors = current.send_data_tcp(
                    UPDATE_SUCC, str(k)).decode()
                remote_successors = remote_successors.split('|')

                for i in range(0, len(remote_successors), 2):
                    ip = remote_successors[i]
                    port = int(remote_successors[i+1])
                    node = NodeReference(ip, port)
                    if node.id not in [n.id for n in successor_list]:  # Evitar duplicados
                        successor_list.append(node)

            except Exception:
                break  # Si hay fallo de conexión, terminamos

            # Avanzamos al siguiente sucesor
            current = current.successor

        return successor_list[:k]  # Retornar solo k nodos



    def update_repli_list(self, id):
        print(f'REPLICANDO {id} EN {self.id}')
        self.repli_pred_list.append(id)
        for element in self.succ_list[:-1]:
            element.send_data_tcp(UPDATE_REPLI_LIST, id)

    def get_succ_list(self, succ_list=None):
        if succ_list is None:
            # Obtiene la lista de sucesores del sucesor
            succ_list = [NodeReference(e, self.tcp_port) for e in self.successor.send_data_tcp(
                LIST_SUCC, f'').decode().split('|')]
        else:
            succ_list = [NodeReference(e, self.tcp_port) for e in succ_list]

        # Crea mi lista de sucesores con mi sucesor mas los primeros k-1 sucesores del sucesor
        self_succ_list = [self.successor]
        for i in range(0, PROPAGATION - 1):
            self_succ_list.append(succ_list[i])
        # Si son iguales significa que ya actualice todas las listas de sucesores
        if self_succ_list == self.succ_list:
            return
        self.succ_list = self_succ_list
        print(
            f"LISTA DE SUCESORES: {[element.id for element in self.succ_list]}")
        st1 = ''
        for e in self.succ_list:
            st1 += f'{e.ip}|'
        response = st1[:-1]
        # Mi predecesor actualiza su lista de sucesores conmigo
        self.predecessor.send_data_tcp(UPDATE_SUCC_LIST, response)

    def get_pred_list(self, pred_list=None):
        print("@@ENTRO@@")
        if pred_list is None:
            # Obtiene la lista de sucesores del sucesor
            pred_list = [NodeReference(e, self.tcp_port) for e in self.predecessor.send_data_tcp(
                LIST_PRED, f'').decode().split('|')]
        else:
            pred_list = [NodeReference(e, self.tcp_port) for e in pred_list]

        # Crea mi lista de predecesores los primeros k-1 predecesores del sucesor
        self_pred_list = [self.predecessor]
        for i in range(0, PROPAGATION - 1):
            self_pred_list.append(pred_list[i])
        # Si son iguales significa que ya actualice todas las listas de sucesores
        if self_pred_list == self.pred_list:
            return
        self.pred_list = self_pred_list
        print(
            f"LISTA DE PREDECESORES: {[element.id for element in self.pred_list]}")
        st1 = ''
        for e in self.pred_list:
            st1 += f'{e.ip}|'
        response = st1[:-1]
        # Mi sucesor actualiza su lista de predecesores conmigo
        self.successor.send_data_tcp(UPDATE_PRED_LIST, response)


if __name__ == "__main__":
    server = ChordNode()
