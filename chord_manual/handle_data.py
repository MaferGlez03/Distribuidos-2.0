from threading import Event
from storage import Contact, Group, User
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
        """
        result = ''
        
        # Obtener todos los usuarios de la base de datos
        users = session.query(User).all()
        for user in users:
            user_id = self.set_id(user.email)  # Usamos el email para generar el ID
            if id is None or (id < self._id and user_id < id) or (id > self._id and user_id > self._id):
                result += f'{user.id}'  # Añadir el ID del usuario
                
                # Añadir los eventos del usuario
                for event in user.events:
                    result += f'/event/{event.id}/{event.name}/{event.date}/{event.privacy}/{event.status}'
                
                # Añadir los contactos del usuario
                for contact in user.contacts:
                    result += f'/contact/{contact.id}/{contact.contact_name}'
                
                # Añadir los grupos del usuario
                for group in user.groups:
                    result += f'/group/{group.id}/{group.name}'
                
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
        users = data.split('|')[:-1]  # Dividir la cadena en usuarios
        for user in users:
            if user != '':
                parts = user.split('/')
                user_id = int(parts[0])  # ID del usuario
                
                # Crear el usuario si no existe
                user_db = session.query(User).filter_by(id=user_id).first()
                if not user_db:
                    user_db = User(id=user_id, name='Unknown', email=f'user{user_id}@example.com', password_hash='')
                    session.add(user_db)
                
                # Procesar los datos del usuario
                i = 1
                while i < len(parts):
                    if parts[i] == 'event':
                        # Crear un evento
                        event_id = int(parts[i + 1])
                        event_name = parts[i + 2]
                        event_date = datetime.strptime(parts[i + 3], '%Y-%m-%d %H:%M:%S')
                        event_privacy = parts[i + 4]
                        event_status = parts[i + 5]
                        
                        event = Event(
                            id=event_id,
                            name=event_name,
                            date=event_date,
                            privacy=event_privacy,
                            status=event_status,
                            owner_id=user_id
                        )
                        session.add(event)
                        i += 6
                    
                    elif parts[i] == 'contact':
                        # Crear un contacto
                        contact_id = int(parts[i + 1])
                        contact_name = parts[i + 2]
                        
                        contact = Contact(
                            id=contact_id,
                            user_id=user_id,
                            contact_name=contact_name
                        )
                        session.add(contact)
                        i += 3
                    
                    elif parts[i] == 'group':
                        # Crear un grupo
                        group_id = int(parts[i + 1])
                        group_name = parts[i + 2]
                        
                        group = Group(
                            id=group_id,
                            name=group_name,
                            owner_id=user_id
                        )
                        session.add(group)
                        i += 3
        
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
