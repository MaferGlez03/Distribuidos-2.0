from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func 

# Configurar la base de datos SQLite
engine = create_engine('sqlite:///agenda.db', echo=False)  # echo=True para ver las consultas SQL en la consola
Base = declarative_base()

# Definir las tablas como clases
class UserAgenda(Base):
    __tablename__ = 'user_agenda'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    user = relationship('User', back_populates='agenda')
    event = relationship('Event', back_populates='agenda_users')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)  # Usamos email en lugar de número
    password_hash = Column(String, nullable=False)  # Contraseña hasheada
    contacts = relationship('Contact', back_populates='user')
    events = relationship('Event', back_populates='owner')
    groups = relationship('Group', back_populates='owner')
    agenda = relationship('UserAgenda', back_populates='user')

    def set_password(self, password: str):
        """
        Hashea la contraseña antes de almacenarla.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verifica si la contraseña es correcta.
        """
        return check_password_hash(self.password_hash, password)
    def normalize_name(self, name: str) -> str:
        """
        Normaliza el nombre para evitar duplicados.
        - Convierte a minúsculas.
        - Elimina espacios al principio y al final.
        """
        return name.lower().strip()

class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner_id = Column(Integer, nullable=False)
    contact_name = Column(String, nullable=False)
    user = relationship('User', back_populates='contacts')

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Dueño del evento
    privacy = Column(Enum('public', 'private', 'group', name='privacy_types'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'))  # Grupo asociado (si es grupal)
    status = Column(Enum('pending', 'confirmed', 'canceled', name='status_types'), nullable=False)
    owner = relationship('User', back_populates='events')
    group = relationship('Group', back_populates='events')
    agenda_users = relationship('UserAgenda', back_populates='event')

    def __str__(self):
        # Formatear la fecha para que sea más legible
        formatted_date = self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date else 'N/A'
        
        # Obtener el nombre del dueño (si está cargada la relación)
        owner_name = self.owner.name if self.owner else 'N/A'
        
        # Obtener el nombre del grupo (si está cargada la relación)
        group_name = self.group.name if self.group else 'N/A'
        
        # Construir la cadena de representación
        return (
            f"Event(id={self.id}, name='{self.name}', date='{formatted_date}', "
            f"owner='{owner_name}', privacy='{self.privacy}', group='{group_name}', "
            f"status='{self.status}')"
        )

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', back_populates='groups')
    members = relationship('GroupMember', back_populates='group')
    events = relationship('Event', back_populates='group')

class GroupMember(Base):
    __tablename__ = 'group_members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    # admin_id = Column(Integer, ForeignKey('admin.id'), nullable=True)  # ID del administrador que añadió al miembro
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Enum('admin', 'member', name='role_types'), nullable=False, default='member')  # Rol del miembro
    group = relationship('Group', back_populates='members')
    user = relationship('User')

# Crear las tablas en la base de datos
Base.metadata.create_all(engine)

# Configurar la sesión
Session = sessionmaker(bind=engine)
session = Session()

# Clase Database para manejar las operaciones
class Database:
    def __init__(self):
        self.session = Session()

    def close(self):
        """
        Cierra la sesión de la base de datos.
        """
        self.session.close()


    def normalize_name(self, name: str) -> str:
        """
        Normaliza el nombre para evitar duplicados.
        - Convierte a minúsculas.
        - Elimina espacios al principio y al final.
        """
        return name.lower().strip()

    def register_user(self, name: str, email: str, password: str):
        """
        Registra un nuevo usuario con contraseña segura.
        Verifica que el nombre no esté duplicado (ignorando mayúsculas, minúsculas y espacios).
        """
        normalized_name = self.normalize_name(name)

        # Verificar si ya existe un usuario con el mismo nombre normalizado
        existing_user = (
            self.session.query(User)
            .filter(func.lower(func.trim(User.name)) == normalized_name)
            .first()
        )

        if existing_user:
            return (False, None)  # El nombre ya está registrado

        # Crear y registrar el nuevo usuario
        user = User(name=name, email=email)
        user.set_password(password)
        self.session.add(user)

        try:
            self.session.commit()
            return user.id, user.name
        except:
            self.session.rollback()
            return None  # El email ya está registrado

    def login_user(self, username: str, password: str) -> dict:
        """
        Inicia sesión de un usuario con autenticación segura.
        """
        user = self.session.query(User).filter_by(name=username).first()
        if user and user.check_password(password):
            return (user.id,username)
        return None

    # Métodos para contactos
    def add_contact(self, user_id: int, contact_name: str, owner_id: int) -> bool:
        """
        Agrega un contacto a un usuario.
        """
        if (contact_name, user_id) in self.list_contacts(owner_id):
            self.session.rollback()
            return False  # El contacto ya existe
        contact = Contact(user_id=user_id, contact_name=contact_name, owner_id=owner_id)
        self.session.add(contact)
        try:
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False  # El contacto ya existe

    def list_contacts(self, user_id: int) -> list:
        """
        Lista los contactos de un usuario.
        """
        contacts = self.session.query(Contact).filter(Contact.owner_id == user_id)
        return [(contact.id, contact.contact_name) for contact in contacts]
    
    def delete_contact(self, contact_id: int) -> bool:
        """
        Elimina un contacto de la lista de contactos de un usuario
        """
        contact = self.session.query(Contact).filter_by(id=contact_id).first()
        if contact:
            self.session.delete(contact)
            self.session.commit()
            return True
        return False  # El miembro no existe en el grupo

    # Métodos para eventos
    def create_event(self, name: str, date: str, owner_id: int, privacy: str, group_id=None) -> bool:
        """
        Crea un nuevo evento.
        """
        event = Event(
            name=name,
            date=datetime.strptime(date, '%Y-%m-%d'),
            owner_id=owner_id,
            privacy=privacy,
            group_id=group_id,
            status='confirmed'
        )
        self.session.add(event)
        try:
            self.session.commit()
            self._add_event_to_agenda(owner_id, event.id)
            return True
        except:
            self.session.rollback()
            return False  # Error al crear el evento

    def create_group_event(self, name: str, date: str, owner_id: int, group_id: int) -> bool:
        """
        Crea un evento grupal. Si el dueño es admin, se añade automáticamente a las agendas de los miembros.
        """
        # Verificar si el dueño es admin del grupo
        is_admin = self.session.query(GroupMember).filter_by(
            group_id=group_id, user_id=owner_id, role='admin'
        ).first() is not None
        print("IS ADMIN: ", is_admin)

        # Crear el evento
        event = Event(
            name=name,
            date=datetime.strptime(date, '%Y-%m-%d'),
            owner_id=owner_id,
            privacy='group',
            group_id=group_id,
            status='confirmed' if is_admin else 'pending'  # Confirmado si es admin
        )
        self.session.add(event)
        self.session.commit()

        # Si es admin, añadir el evento a las agendas de los miembros
        if is_admin:
            members = self.session.query(GroupMember).filter_by(group_id=group_id).all()
            for member in members:
                if not self._has_event_conflict(member.user_id, event.date):
                    self._add_event_to_agenda(member.user_id, event.id)

        return True


    def confirm_event(self, event_id: int) -> bool:
        """
        Confirma un evento.
        """
        event = self.session.query(Event).filter_by(id=event_id).first()
        if event:
            event.status = 'confirmed'
            self.session.commit()
            return True
        return False

    def cancel_event(self, event_id: int) -> bool:
        """
        Cancela un evento.
        """
        event = self.session.query(Event).filter_by(id=event_id).first()
        if event:
            event.status = 'canceled'
            self.session.commit()
            return True
        return False

    def list_events(self, user_id: int) -> list:
        """
        Lista los eventos de un usuario (personales y grupales).
        """
        # events = self.session.query(Event).filter(
        #     (Event.owner_id == user_id) | ((Event.group_id.in_(
        #         [l[0] for l in [g for g in self.session.query(GroupMember.group_id).filter_by(user_id=user_id)]]
        #     )) & Event.status == 'confirmed')
        # ).all()
        # lista = [l[0] for l in [g for g in self.session.query(GroupMember.group_id).filter_by(user_id=user_id)]]
        # print("GRUPOS DE LOS QUE SOY MIEMBRO: ", lista)
        # print("TODOS LOS EVENTOS: ", [(e.group_id, e.name, e.group_id, e.status) for e in self.session.query(Event)])
        # print("CONSULTA: ", [(e.group_id, e.name, e.status) for e in events])
        # # print(f"COMPRUEBA: {type(lista[0])} {lista[0]} {1 in lista}")
        # Subconsulta para obtener los group_id asociados al user_id
        subquery = self.session.query(GroupMember.group_id).filter_by(user_id=user_id).scalar_subquery()

        # Consulta principal
        events = self.session.query(Event).filter(
            (Event.owner_id == user_id) |  # El usuario es el propietario
            (
                (Event.group_id.in_(subquery)) &  # El usuario pertenece a un grupo asociado al evento
                (Event.status == 'confirmed')  # El evento está confirmado
            )
        ).all()
        return events
    
    def list_events_pending(self, user_id: int) -> list:
        """
        Lista los eventos de un usuario (personales y grupales).
        """
        print(user_id)
        events = self.session.query(Event).filter((Event.group_id.in_(
                self.session.query(GroupMember.group_id).filter_by(user_id=user_id)
            )) & (Event.status == 'pending')
        ).all()
        return events

    # Métodos para grupos
    def create_group(self, name: str, owner_id: int) -> bool:
        """
        Crea un nuevo grupo.
        """
        group = Group(name=name, owner_id=owner_id)
        self.session.add(group)
        try:
            self.session.commit()
            self._add_member_to_group(group.id, owner_id, 'admin')
            return True
        except:
            self.session.rollback()
            return False  # El grupo ya existe

    def add_member_to_group(self, group_id: int, user_id: int, role: str = 'member') -> bool:
        """
        Agrega un miembro a un grupo.
        """
        user_db = session.query(Contact).filter_by(id=user_id).first()

        if (user_db.user_id, self.getUsername(user_db.user_id,)) in self.list_members(group_id):
            self.session.rollback()
            return False  # El usuario ya está en el grupo
        
        member = GroupMember(group_id=group_id, user_id=user_db.user_id, role=role)
        self.session.add(member)
        try:
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False  # El usuario ya está en el grupo
        
    def _add_member_to_group(self, group_id: int, user_id: int, role: str = 'member') -> bool:
        """
        Agrega un miembro a un grupo.
        """
        

        if (user_id, self.getUsername(user_id,)) in self.list_members(group_id):
            self.session.rollback()
            return False  # El usuario ya está en el grupo
        
        member = GroupMember(group_id=group_id, user_id=user_id, role=role)
        self.session.add(member)
        try:
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False  # El usuario ya está en el grupo
        
    def remove_member_from_group(self, group_id: int, user_id: int, admin_id: int) -> bool:
        """
        Elimina un miembro de un grupo.
        """
        member = self.session.query(GroupMember).filter_by(group_id=group_id, user_id=user_id).first()
        role = self.session.query(GroupMember).filter_by(group_id=group_id, user_id=admin_id).first().role
        if member:
            if role == 'admin' and admin_id != user_id:
                self.session.delete(member)
                self.session.commit()
                return True
            return False
        return False # El miembro no existe en el grupo

    def list_groups(self, user_id: int) -> list:
        """
        Lista los grupos de un usuario.
        """
        print(user_id)
        groups = self.session.query(GroupMember).filter(GroupMember.user_id == user_id).all()
        print(groups)
        group_ids = [group.group_id for group in groups]
        print(group_ids)
        group_names = [group.name for group in [x for x in [self.session.query(Group).filter(Group.id == group_id).first() for group_id in group_ids] if x is not None]]
        print(group_names)
        final = list(zip(group_ids, group_names))
        print(final)
        return final

    def list_members(self, group_id: int) -> list:
        """
        Lista los miembros de un grupo
        """
        members = self.session.query(GroupMember).filter(GroupMember.group_id == group_id).all()
        return [(member.user_id, self.getUsername(member.user_id)) for member in members]
    
    def delete_group(self, group_id: int) -> bool:
        """
        Elimina un grupo
        """
        group = self.session.query(Group).filter_by(id=group_id).first()
        if group:
            members = [member[0] for member in self.list_members(group.id)]
            if len(members) < 1:
                self.session.delete(group)
                self.session.commit()
                return True
            for member in members: self.remove_member_from_group(group.id, member, group.owner_id)
            self.leave_group(group.id, group.owner_id)
            self.session.delete(group)
            self.session.commit()
            return True
        return False  # El grupo no existe
    
    def leave_group(self, group_id: int, user_id: int) -> bool:
        """
        Abandona un grupo
        """
        groupMember = self.session.query(GroupMember).filter_by(group_id=group_id, user_id=user_id).first()
        if not groupMember:
            return False  # El grupo no existe
        members = self.session.query(GroupMember).filter(GroupMember.group_id == group_id).all()
        if len(members) <= 1:
            if groupMember.role == 'admin':
                groupMember.role = 'member'
                return self.leave_group(group_id, user_id)
            else: # no soy admin
                self.session.delete(groupMember)
                self.session.commit()
                return self.delete_group(group_id)
        else: # varios miembros
            if groupMember.role == 'admin':
                for member in members:
                    if member.role == 'member':
                        member.role = 'admin'
                        self.session.delete(groupMember)
                        self.session.commit()
                        return True
            else: # no soy admin
                self.session.delete(groupMember)
                self.session.commit()
                return True

    # Métodos auxiliares
    def _has_event_conflict(self, user_id: int, event_date: datetime) -> bool:
        """
        Verifica si un usuario tiene un evento en la misma fecha.
        """
        return self.session.query(Event).filter(
            (Event.owner_id == user_id) & (Event.date == event_date)
        ).first() is not None

    def _add_event_to_agenda(self, user_id: int, event_id: int) -> bool:
        """
        Añade un evento a la agenda de un usuario.
        """
        # Verificar si el evento ya está en la agenda del usuario
        existing_entry = self.session.query(UserAgenda).filter_by(user_id=user_id, event_id=event_id).first()
        if existing_entry:
            return False  # El evento ya está en la agenda

        # Añadir el evento a la agenda del usuario
        agenda_entry = UserAgenda(user_id=user_id, event_id=event_id)
        self.session.add(agenda_entry)
        self.session.commit()
        return True
    
    def list_personal_agenda(self, user_id: int) -> list:
        """Lista todos los eventos de un usuario con su nombre y hora."""
        events = self.session.query(Event).filter(
            (Event.owner_id == user_id) |  # Eventos creados por el usuario
            (Event.id.in_(  # Eventos en los que el usuario está invitado
                self.session.query(UserAgenda.event_id).filter_by(user_id=user_id)
            ))
        ).all()

        # Formatear la salida
        agenda = []
        for event in events:
            agenda.append({
                'id': event.id,
                'name': event.name,
                'date': event.date.strftime('%Y-%m-%d %H:%M:%S'),  # Formato de fecha y hora
                'privacy': event.privacy,
                'status': event.status
            })
        return agenda
    
    def list_group_agenda(self, group_id: int, user_id: int) -> list:
        """Lista todos los eventos de un grupo al que pertenece el usuario."""
        # Verificar si el usuario es miembro del grupo
        is_member = self.session.query(GroupMember).filter_by(
            group_id=group_id, user_id=user_id
        ).first() is not None

        if not is_member:
            return []  # El usuario no es miembro del grupo

        # Obtener los eventos del grupo
        events = self.session.query(Event).filter_by(group_id=group_id).all()

        # Formatear la salida
        agenda = []
        for event in events:
            agenda.append({
                'id': event.id,
                'name': event.name,
                'date': event.date.strftime('%Y-%m-%d %H:%M:%S'),  # Formato de fecha y hora
                'privacy': event.privacy,
                'status': event.status,
                'owner_id': event.owner_id
            })
        return agenda

    def getUserID(self, username):
        user = self.session.query(User).filter_by(name=username).first()
        if user:
            return user.id
        return None
    
    def getUsername(self, id):
        user = self.session.query(User).filter_by(id=id).first()
        if user:
            return user.name
        return None
    
    def getGroupID(self, name):
        group = self.session.query(Group).filter_by(name=name).first()
        if group:
            return group.id
        return None
    