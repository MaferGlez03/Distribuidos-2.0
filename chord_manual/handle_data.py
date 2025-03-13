from storage import Contact, Group, User, GroupMember, Event, UserAgenda
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime
import os

# Configurar la conexión a la base de datos
engine = create_engine('sqlite:///agenda.db')
Session = sessionmaker(bind=engine)
session = Session()

class HandleData:
    def __init__(self, id: int):
        self.garbage = []  # Lista de datos a eliminar
        self.id = id       # ID del nodo actual

    def data(self, delete: bool, id=None) -> str:
        """
        Recupera los datos de un usuario según su ID y los devuelve en un formato específico.
        Si delete es True, elimina los datos recuperados. 
        Si ID es None recupera de todos los usuarios
        """
        result = ''
        
        # Obtener todos los usuarios de la base de datos con relaciones cargadas
        users = session.query(User).options(
            joinedload(User.contacts),  # Cargar contactos
            joinedload(User.events),    # Cargar eventos
            joinedload(User.agenda),  # Cargar contactos
            joinedload(User.groups),    # Cargar eventos
        ).all()
        for user in users:
            user_id = self.set_id(user.email)  # Usamos el email para generar el ID
            print(f"USUARIO: {user_id} | DUEÑO: {self.id}")
            print(f"Numero de contactos: {len(user.contacts)}")
            print(f"Numero de eventos: {len(user.events)}")
            print(f"Numero de agendas: {len(user.agenda)}")
            print(f"Numero de grupos: {len(user.groups)}")
            if id is None or (id <= self.id and user_id <= id) or (id >= self.id and user_id >= self.id and user_id <= id) or (id <= self.id and user_id >= self.id):
                result += f'{user.id}|{user.name}|{user.email}|{user.password_hash}¡¡'  # Añadir al usuario
                
                # Añadir los eventos del usuario
                for contact in user.contacts:
                    result += 'contacts¡'
                    result += f'{contact.id}|{contact.user_id}|{contact.owner_id}|{contact.contact_name}||'
                
                # Añadir los contactos del usuario
                for event in user.events:
                    result += 'events¡'
                    result += f'{event.id}|{event.name}|{event.date}|{event.owner_id}|{event.privacy}|{event.group_id}|{event.status}||'
                
                # Añadir los miembros de grupos del usuario
                for agenda in user.agenda:
                    result += 'agenda¡'
                    result += f'{agenda.id}|{agenda.user_id}|{agenda.event_id}||'
                
                # Añadir los grupos del usuario
                for group in user.groups:
                    result += 'groups¡'
                    result += f'{group.id}|{group.name}|{group.owner_id}||'
                    for member in group.members:
                        result += 'member¡'
                        result += f'{member.id}|{member.group_id}|{member.user_id}|{member.role}||'
                
                if result[-1] != '¡': result += '|'
                else: result += '|||'
                self.garbage.append(user.id)  # Añadir el usuario a la lista de garbage
        
        # Eliminar los datos si delete es True
        self._clean(delete)
        return result

    @classmethod
    def create(cls, data: str):
        """
        Crea datos en la base de datos a partir de una cadena formateada.
        """
        if len(data) == 0:
            return
        print("data", data)
        users = list(filter(None, data.split('|||')))  # Dividir la cadena en usuarios
        print("users", users)
        for user in users:
            if user != '':
                user_data = list(filter(None, user.split('¡¡')))  # Dividir en datos del usuario, data
                print("user_data", user_data)
                user1 = list(filter(None, user_data[0].split('|')))  # Datos del Usuario
                print("user1", user1)
                user_id = user1[0]
                print(user_id)
                if len(user_data) > 1:
                    data = user_data[1]
                    print(data)
                    tablas = list(filter(None, data.split('||')))
                    print(tablas)
                else:
                    tablas = ''
                # Crear el usuario si no existe
                user_db = session.query(User).filter_by(id=user_id).first()
                if not user_db:
                    user_db = User(id=user_id, name=user1[1], email=user1[2], password_hash=user1[3])
                    session.add(user_db)
                
                if tablas == '':
                    session.commit()
                    continue
                # Procesar los datos del usuario
                listica = [list(filter(None, tabla.split('¡'))) for tabla in tablas]
                print(f"listica: {listica}")
                for titulo, content in [list(filter(None, tabla.split('¡'))) for tabla in tablas]:
                    info = list(filter(None, content.split('|')))
                    if titulo == 'events':
                        # Crear un evento
                        event_id = int(info[0])
                        event_name = info[1]
                        event_date = datetime.strptime(info[2], '%Y-%m-%d %H:%M:%S')
                        event_owner_id = int(info[3])
                        event_privacy = info[4]
                        event_group_id = int(info[5]) if isinstance(info[5], str) and info[5].isdigit() else None
                        event_status = info[6]

                        event0 = session.query(Event).filter_by(id=event_id).first()
                        if not event0:
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

                        contact0 = session.query(Contact).filter_by(id=contact_id).first()
                        if not contact0:
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

                        group0 = session.query(Group).filter_by(id=group_id).first()
                        if not group0:
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

                        group_member0 = session.query(GroupMember).filter_by(id=group_id).first()
                        if not group_member0:
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
            for user_id in self.garbage:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    # Eliminar eventos, contactos y grupos del usuario
                    session.query(Event).filter_by(owner_id=user_id).delete()
                    session.query(Contact).filter_by(user_id=user_id).delete()
                    session.query(Group).filter_by(owner_id=user_id).delete()
                    session.query(UserAgenda).filter_by(user_id=user_id).delete()
                    session.query(GroupMember).filter_by(user_id=user_id).delete()
                    session.delete(user)
            
            # Guardar los cambios en la base de datos
            session.commit()
        
        # Reiniciar la lista de garbage
        self.garbage = []

    def set_id(self, data: str) -> int:
        """
        Hashea una cadena usando SHA-1 y devuelve un entero.
        """
        return int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 8)
