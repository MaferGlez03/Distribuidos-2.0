from threading import Event
from storage import Contact, Group, User, GroupMember
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Configurar la conexión a la base de datos
engine = create_engine('sqlite:///agenda.db')
Session = sessionmaker(bind=engine)
session = Session()

class HandleData:
    def __init__(self, id: int):
        self._garbage = []  # Lista de datos a eliminar
        self._id = id       # ID del nodo actual

    def data(self, delete: bool, id=None) -> str:
        """
        Recupera los datos de un usuario según su ID y los devuelve en un formato específico.
        Si delete es True, elimina los datos recuperados. 
        Si ID es None recupera de todos los usuarios
        """
        result = ''
        
        # Obtener todos los usuarios de la base de datos
        users = session.query(User).all()
        for user in users:
            user_id = self.set_id(user.email)  # Usamos el email para generar el ID
            if id is None or (id < self._id and user_id < id) or (id > self._id and user_id > self._id):
                result += f'{user.id}|{user.name}|{user.email}|{user.password_hash}$'  # Añadir al usuario
                
                # Añadir los eventos del usuario
                result += 'contacts/'
                for contact in user.contacts:
                    result += f'{contact.id}|{contact.user_id}|{contact.owner.id}|{contact.contact_name}||'
                
                # Añadir los contactos del usuario
                result += 'events/'
                for event in user.events:
                    result += f'{event.id}|{event.name}|{event.date}|{event.owner_id}|{event.privacy}|{event.group_id}|{event.status}||'
                
                # Añadir los miembros de grupos del usuario
                result += 'group_members/'
                for group in user.group_members:
                    result += f'{group.id}|{group.group_id}|{group.user_id}|{group.role}||'
                
                # Añadir los grupos del usuario
                result += 'groups/'
                for group in user.groups:
                    result += f'{group.id}|{group.name}|{group.owner_id}||'
                
                result += '|'
                self._garbage.append(user.id)  # Añadir el usuario a la lista de garbage
        
        # Eliminar los datos si delete es True
        self._clean(delete)
        return result

    @classmethod
    def create(cls, data: str):
        """
        Crea datos en la base de datos a partir de una cadena formateada.
        """
        users = data.split('|||')  # Dividir la cadena en usuarios
        for user in users:
            if user != '':
                user_data = user.split('$')  # Dividir en datos del usuario, data
                user = user_data[0].split('|')  # Datos del Usuario
                user_id = user[0]
                data = user_data[1]
                tablas = data.split('||')
                
                # Crear el usuario si no existe
                user_db = session.query(User).filter_by(id=user_id).first()
                if not user_db:
                    user_db = User(id=user_id, name=user[1], email=user[2], password_hash=user[3])
                    session.add(user_db)
                

                # Procesar los datos del usuario
                for titulo, info in [tabla.split('/') for tabla in tablas]:
                    if titulo == 'events':
                        # Crear un evento
                        event_id = int(info[0])
                        event_name = info[1]
                        event_date = datetime.strptime(info[2], '%Y-%m-%d %H:%M:%S')
                        event_owner_id = int(info[3])
                        event_privacy = info[4]
                        event_group_id = int(info[5])
                        event_status = info[6]
                        
                        event = Event(
                            id=event_id,
                            name=event_name,
                            date=event_date,
                            owner_id=event_owner_id,
                            privacy=event_privacy,
                            group_id=event_group_id,
                            status=event_status,
                        )
                        session.add(event)
                    
                    elif titulo == 'contacts':
                        # Crear un contacto
                        contact_id = int(info[0])
                        contact_user_id = int(info[1])
                        contact_owner_id = int(info[2]) # Se cambia por user_id
                        contact_name = info[3]
                        
                        contact = Contact(
                            id=contact_id,
                            user_id=contact_user_id,
                            owner_id=user_id,
                            contact_name=contact_name
                        )
                        session.add(contact)
                    
                    elif titulo == 'groups':
                        # Crear un grupo
                        group_id = int(info[0]),
                        group_name = info[1],
                        group_owner_id = int(info[2]) # Se cambia por user_id
                        
                        group = Group(
                            id=group_id,
                            name=group_name,
                            owner_id=user_id
                        )
                        session.add(group)

                    elif titulo == 'group_members':
                        # Crear un group member
                        group_id = int(info[0])
                        group_group_id = int(info[1])
                        group_user_id = int(info[2]) #  Se cambia por user_id
                        group_role = info[3]

                        group_member = GroupMember(
                            id=group_id,
                            group_id=group_group_id,
                            user_id=user_id,
                            role=group_role
                        )
                        session.add(group_member)
        
        # Guardar los cambios en la base de datos
        session.commit()

    def _clean(self, delete: bool):
        """
        Elimina los datos de la base de datos que están en la lista _garbage.
        """
        if delete:
            for user_id in self._garbage:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    # Eliminar eventos, contactos y grupos del usuario
                    session.query(Event).filter_by(owner_id=user_id).delete()
                    session.query(Contact).filter_by(user_id=user_id).delete()
                    session.query(Group).filter_by(owner_id=user_id).delete()
                    session.delete(user)
            
            # Guardar los cambios en la base de datos
            session.commit()
        
        # Reiniciar la lista de garbage
        self._garbage = []

    def set_id(data: str) -> int:
        """
        Hashea una cadena usando SHA-1 y devuelve un entero.
        """
        return int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 8)
