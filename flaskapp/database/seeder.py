# flaskapp/database/seeder.py

import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.exc import IntegrityError

from flaskapp import db
from flaskapp.database.models import (
    User, Organization, OrganizationMember, Activity, ActivityCategory,
    Event, Tournament, Team, TeamMember, TournamentReferee,
    EventStatus, TournamentStatus, MatchStatus, TeamInvitationStatus,
    NotificationType, RelatedEntityType
)

# Configuración inicial
fake = Faker('es_CL')
NUM_USERS = 669
NUM_ORGANIZATIONS = 18
NUM_ACTIVITIES = 5
PASSWORD = "password1" # Contraseña común para desarrollo

def seed_database(app):
    """
    Función principal para poblar la base de datos con datos de prueba.
    Utiliza el ORM de SQLAlchemy para crear objetos y manejar relaciones.
    """
    with app.app_context():
        # 1. Verificar si la base de datos ya tiene datos
        if db.session.query(User).first():
            print("Saltando el proceso de seeding: La base de datos ya contiene usuarios.")
            return

        print("Iniciando el proceso de seeding...")
        try:
            # 2. Crear datos maestros (tablas de estado, tipos, categorías)
            print("Creando datos maestros (estados, tipos, etc.)...")
            seed_master_data()

            # 3. Crear entidades principales en orden de dependencia
            print(f"Generando {NUM_ACTIVITIES} actividades...")
            activities = create_activities(NUM_ACTIVITIES)

            print(f"Generando {NUM_USERS} usuarios...")
            users, admins = create_users(NUM_USERS)

            print(f"Generando {NUM_ORGANIZATIONS} organizaciones...")
            organizations = create_organizations(NUM_ORGANIZATIONS, admins)
            
            print("Asignando miembros a las organizaciones...")
            # 'organization_members' es una lista de objetos OrganizationMember
            organization_members = assign_members_to_organizations(organizations, users)

            print("Generando eventos y torneos...")
            # Esta función ahora también crea equipos y árbitros
            create_events_and_tournaments(organizations, activities, organization_members)

            # 4. Confirmar todos los cambios en la base de datos
            db.session.commit()
            print("\n¡Seeding completado exitosamente! ✅")

        except IntegrityError as e:
            db.session.rollback()
            print(f"\nError de integridad durante el seeding: {e}")
            print("Se ha revertido la transacción. La base de datos está en su estado original.")
        except Exception as e:
            db.session.rollback()
            print(f"\nOcurrió un error inesperado durante el seeding: {e}")
            print("Se ha revertido la transacción.")

def seed_master_data():
    """Crea los registros en las tablas de estado y tipo."""
    statuses_data = {
        EventStatus: [
            {'code': 'PLANNED', 'description': 'Evento planificado, aún no ha comenzado.'},
            {'code': 'IN_PROGRESS', 'description': 'Evento en curso.'},
            {'code': 'COMPLETED', 'description': 'Evento finalizado.'},
            {'code': 'CANCELLED', 'description': 'Evento cancelado.'},
        ],
        TournamentStatus: [
            {'code': 'REGISTRATION_OPEN', 'description': 'Inscripciones abiertas.'},
            #{'code': 'REGISTRATION_CLOSED', 'description': 'Inscripciones cerradas.'},
            {'code': 'IN_PROGRESS', 'description': 'Torneo en curso.'},
            {'code': 'COMPLETED', 'description': 'Torneo finalizado.'},
            {'code': 'CANCELLED', 'description': 'Torneo cancelado.'},
        ],
        MatchStatus: [
            {'code': 'PENDING', 'description': 'Partido pendiente de jugarse.'},
            {'code': 'COMPLETED', 'description': 'Partido finalizado con resultado.'},
        ],
        TeamInvitationStatus: [
            {'code': 'PENDING', 'description': 'Invitación pendiente de respuesta.'},
            {'code': 'ACCEPTED', 'description': 'Invitación aceptada.'},
            {'code': 'REJECTED', 'description': 'Invitación rechazada.'},
        ],
        NotificationType: [
            {'code': 'TEAM_INVITE', 'description': 'Invitación a equipo.'}
        ],
        RelatedEntityType: [
            {'name': 'Team'},
            {'name': 'Tournament'}
        ],
        ActivityCategory: [
            {'name': 'eSports'},
            {'name': 'Deportes Tradicionales'}
        ]
    }

    for model, data_list in statuses_data.items():
        for data in data_list:
            instance = model(**data)
            db.session.add(instance)
    
    # Hacemos flush para que los IDs estén disponibles para el resto del script
    db.session.flush()

def create_users(num_users):
    """Genera usuarios y los divide en administradores y usuarios normales."""
    
    users = []
    admins = []
    
    for i in range(1, num_users + 1):
        is_admin = i <= 5 # Los primeros 5 son administradores

        # Nombre y foto de perfil según el género
        if i % 2 == 0:
            f_name = fake.name_female()
            f_profile_pic = f"https://randomuser.me/api/portraits/women/{i % 100}.jpg"
        else:
            f_name = fake.name_male()
            f_profile_pic = f"https://randomuser.me/api/portraits/mans/{i % 100}.jpg"
            
        user = User(
            name=f_name,
            email=f"usuario{i}@{fake.domain_name()}",
            password=PASSWORD,
            profile_picture=f_profile_pic,
            is_admin=is_admin,
            created_at=fake.date_time_between(start_date='-2y', end_date='now')
        )
        db.session.add(user)
        users.append(user)
        if is_admin:
            admins.append(user)
    
    db.session.flush() # Para obtener los IDs de los usuarios
    return users, admins

def create_activities(num_activities):
    """Genera actividades de ejemplo."""
    esports_category = db.session.query(ActivityCategory).filter_by(name='eSports').one()
    
    activity_names = ['League of Legends', 'Valorant', 'Counter-Strike 2', 'EA FC 25', 'Dota 2', 'Overwatch 2']
    min_players = {'League of Legends': 5, 'Valorant': 5, 'Counter-Strike 2': 5, 'EA FC 25': 1, 'Dota 2': 5, 'Overwatch 2': 5}
    
    activities = []
    for name in random.sample(activity_names, num_activities):
        activity = Activity(
            name=name,
            description=fake.paragraph(nb_sentences=2),
            min_players_per_team=min_players.get(name, 1),
            category=esports_category,
            is_active=True
        )
        db.session.add(activity)
        activities.append(activity)
        
    db.session.flush()
    return activities

def create_organizations(num_orgs, admins):
    """Genera organizaciones, asignando un administrador como creador."""
    orgs = []
    org_names = set()
    while len(org_names) < num_orgs:
        org_names.add(f"{fake.company()} eSports")

    for name in org_names:
        org = Organization(
            name=name,
            description=fake.paragraph(nb_sentences=3),
            creator=random.choice(admins), # Usamos el objeto User directamente
            created_at=fake.date_time_between(start_date='-1y', end_date='-6m')
        )
        db.session.add(org)
        orgs.append(org)
        
    db.session.flush()
    return orgs

def assign_members_to_organizations(organizations, users):
    """Asigna usuarios a organizaciones, definiendo roles."""
    all_memberships = []
    for org in organizations:
        # 1. El creador es siempre organizador
        # TODO: Pendiente revisión de concepto. 
        #   ¿Es necesario que el administrador sea parte de la organización?
        """
        creator_membership = OrganizationMember(
            organization=org,
            user=org.creator,
            is_organizer=True,
            joined_at=org.created_at
        )
        db.session.add(creator_membership)
        all_memberships.append(creator_membership)
        """

        # 2. Asignar entre 25 y 125 miembros más.
        potential_members = [u for u in users if u.id != org.creator.id]
        num_members = random.randint(20, 80)
        members_to_add = random.sample(potential_members, min(num_members, len(potential_members)))
        
        first_is_organizer = True  # El primer miembro siempre será organizador
        for user in members_to_add:
            # 10% de probabilidad de ser organizador
            if first_is_organizer: 
                is_organizer = True
                first_is_organizer = False
            else:
                is_organizer = random.random() < 0.1
            membership = OrganizationMember(
                organization=org,
                user=user,
                is_organizer=is_organizer,
                joined_at=fake.date_time_between_dates(datetime_start=org.created_at)
            )
            db.session.add(membership)
            all_memberships.append(membership)
            
    db.session.flush()
    return all_memberships


def create_events_and_tournaments(organizations, activities, all_memberships):
    """Crea eventos y torneos para cada organización."""
    event_status_planned = db.session.query(EventStatus).filter_by(code='PLANNED').one()
    tourney_status_reg_open = db.session.query(TournamentStatus).filter_by(code='REGISTRATION_OPEN').one()

    # Mapear organización a sus miembros para fácil acceso
    org_member_map = {}
    for m in all_memberships:
        if m.organization_id not in org_member_map:
            org_member_map[m.organization_id] = []
        org_member_map[m.organization_id].append(m)

    # Extraer organizadores de cada organización
    for org in organizations:
        # Debug: Verificar org
        print(f"Procesando organización: {org})")
        org_members = org_member_map.get(org.id, [])
        organizers = [m.user for m in org_members if m.is_organizer]
        if not organizers:
            continue

        # Crear 1-3 eventos por organización
        used_event_names = set()  # Para evitar duplicados
        for _ in range(random.randint(1, 3)):
            # Asegurarse de que el nombre del evento sea único
            while True:
                event_name = f"Evento {fake.word().capitalize()} de {fake.historic_people_street_name()}"
                if event_name not in used_event_names:
                    used_event_names.add(event_name)
                    break
            try:
                start = fake.date_time_this_year(after_now=True)
                event = Event(
                    organization=org,
                    name=event_name,
                    description=fake.sentence(),
                    start_date=start,
                    end_date=start + timedelta(days=random.randint(2, 7)),
                    status=event_status_planned,
                    creator=random.choice(organizers)
                )
                db.session.add(event)
            except IntegrityError as e:
                print(f"Error al crear evento: {e}. Saltando este evento.")
                continue
        
        db.session.flush() # Obtener IDs de eventos

        # Crear 2-5 torneos por organización
        for _ in range(random.randint(2, 5)):
            organizer = random.choice(organizers)
            # 70% de los torneos pertenecen a un evento
            linked_event = random.choice(org.events) if org.events and random.random() < 0.7 else None
            
            start = fake.date_time_this_year(after_now=True)
            tourney = Tournament(
                organization=org,
                event=linked_event,
                activity=random.choice(activities),
                name=f"Copa {fake.word().capitalize()} de {org.name}",
                description=fake.paragraph(nb_sentences=4),
                max_teams=random.choice([4, 8, 16]),
                start_date=start,
                end_date=start + timedelta(days=random.randint(1, 14)),
                status=tourney_status_reg_open,
                creator=organizer
            )
            db.session.add(tourney)
            db.session.flush() # Obtenemos el ID del torneo para los equipos

            # Crear equipos y árbitros para este torneo
            print(f"Creando participantes para el torneo: {tourney.name} (ID: {tourney.id})")
            create_tournament_participants(tourney, org_members, organizer)
    
    db.session.flush()

def create_tournament_participants(tournament, org_members, organizer):
    """Puebla un torneo con árbitros y equipos."""
    
    # 1. Asignar 2-4 árbitros
    potential_referees = [m.user for m in org_members]
    num_referees = random.randint(2, 4)
    referees_to_add = random.sample(potential_referees, min(num_referees, len(potential_referees)))
    
    for ref_user in referees_to_add:
        referee = TournamentReferee(
            tournament=tournament,
            user=ref_user,
            assigned_by_user=organizer
        )
        db.session.add(referee)

    # 2. Crear equipos
    # Usuarios que pueden participar (no son árbitros de este torneo)
    referee_ids = {r.id for r in referees_to_add}
    potential_players = [m.user for m in org_members if m.user.id not in referee_ids]
    
    # Inscribir entre 2 y (max_teams - 2) equipos
    num_teams_to_create = random.randint(2, tournament.max_teams - 2)

    for _ in range(num_teams_to_create):
        if not potential_players:
            break # No quedan jugadores disponibles
        
        # El líder del equipo
        team_leader = random.choice(potential_players)
        potential_players.remove(team_leader) # No puede estar en otro equipo

        team = Team(
            tournament=tournament,
            name=f"{fake.company_prefix()} Gaming {fake.company_suffix()} {random.randint(1,100)}",
            seed_score=random.randint(100, 2000)
        )
        db.session.add(team)
        db.session.flush() # Obtener ID del equipo

        # Añadir al líder como miembro
        leader_member = TeamMember(team=team, user=team_leader, is_leader=True)
        db.session.add(leader_member)

        # Añadir más miembros (equipo completo o incompleto)
        min_players = tournament.activity.min_players_per_team
        # Hacemos que algunos equipos estén incompletos
        players_to_add_count = random.randint(min_players // 2, min_players + 2)
        
        if len(potential_players) >= players_to_add_count:
            other_members = random.sample(potential_players, players_to_add_count)
            for member_user in other_members:
                team_member = TeamMember(team=team, user=member_user, is_leader=False)
                db.session.add(team_member)
                potential_players.remove(member_user)