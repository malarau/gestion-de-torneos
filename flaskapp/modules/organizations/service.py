from datetime import datetime
from flask import request
from flask_login import current_user
from typing import List

from sqlalchemy import case
from flaskapp.database.models import Activity, Event, Tournament, TournamentStatus, User, db, Organization, OrganizationMember
from .dto import EventDTO, MemberDTO, OrganizationDTO, OrganizationDetailDTO, OrganizationGroupsDTO, OrganizationListDTO, PaginatedOrganizationsDTO, TournamentDTO

def convert_to_dto(org: Organization, is_member: bool = False, is_organizer: bool = False) -> OrganizationDTO:
    return OrganizationDTO(
        id=org.id,
        name=org.name,
        description=org.description[:100] + '...' if org.description and len(org.description) > 100 else org.description or '',
        member_count=len(org.members),  # Asume relación backref 'members'
        is_organizer=is_organizer,
        is_member=is_member,
        created_at=org.created_at.strftime('%Y-%m-%d')
    )

class OrganizationService:
    @staticmethod
    def get_organization_groups() -> tuple[PaginatedOrganizationsDTO, PaginatedOrganizationsDTO]:
        # Obtener parámetros de paginación para cada tabla
        my_orgs_page = request.args.get('my_orgs_page', 1, type=int)
        other_orgs_page = request.args.get('other_orgs_page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Obtener membresías del usuario
        user_memberships = db.session.query(
            OrganizationMember.organization_id,
            OrganizationMember.is_organizer
        ).filter(
            OrganizationMember.user_id == current_user.id
        ).all()

        member_org_ids = {org_id for org_id, _ in user_memberships}
        organizer_org_ids = {org_id for org_id, is_org in user_memberships if is_org}

        # Consulta base optimizada
        base_query = Organization.query.options(
            db.joinedload(Organization.members)
        )

        # Mis organizaciones (paginación independiente)
        my_orgs_paginated = base_query.filter(
            Organization.id.in_(member_org_ids)
        ).order_by(
            case(
                (Organization.id.in_(organizer_org_ids), 0),
                else_=1
            ),
            Organization.name
        ).paginate(
            page=my_orgs_page,
            per_page=per_page,
            error_out=False
        )

        # Otras organizaciones (paginación independiente)
        other_orgs_paginated = base_query.filter(
            ~Organization.id.in_(member_org_ids)
        ).order_by(
            Organization.name
        ).paginate(
            page=other_orgs_page,
            per_page=per_page,
            error_out=False
        )

        def convert_to_dto(org: Organization) -> OrganizationDTO:
            return OrganizationDTO(
                id=org.id,
                name=org.name,
                description=org.description[:100] + '...' if org.description and len(org.description) > 100 else org.description or '',
                member_count=len(org.members),
                is_organizer=org.id in organizer_org_ids,
                is_member=org.id in member_org_ids,
                created_at=org.created_at.strftime('%Y-%m-%d')
            )

        def to_paginated_dto(paginated_orgs) -> PaginatedOrganizationsDTO:
            return PaginatedOrganizationsDTO(
                items=[convert_to_dto(org) for org in paginated_orgs.items],
                page=paginated_orgs.page,
                per_page=paginated_orgs.per_page,
                total=paginated_orgs.total,
                pages=paginated_orgs.pages
            )

        return (
            to_paginated_dto(my_orgs_paginated),
            to_paginated_dto(other_orgs_paginated)
        )
    
    """ Detalles de una organización específica """
    @staticmethod
    def get_organization_details(organization_id: int, user_id: int) -> OrganizationDetailDTO:
        # Obtener organización básica
        org = Organization.query.options(
            db.joinedload(Organization.creator),
            db.joinedload(Organization.members)
        ).get_or_404(organization_id)

        # Obtener eventos activos (que incluyen hoy en su rango de fechas)
        today = datetime.utcnow().date()
        active_events = Event.query.filter(
            Event.organization_id == organization_id,
            Event.start_date <= today,
            Event.end_date >= today
        ).order_by(Event.start_date.desc()).all()

        # Obtener torneos activos (no completados ni cancelados)
        active_statuses = ['pending', 'in_progress', 'paused']
        active_tournaments = Tournament.query.join(
            TournamentStatus,
            Tournament.status_id == TournamentStatus.id
        ).filter(
            Tournament.organization_id == organization_id,
            TournamentStatus.code.in_(active_statuses)
        ).order_by(Tournament.start_date.desc()).all()

        # Obtener torneos pasados (completados)
        past_tournaments = Tournament.query.join(
            TournamentStatus,
            Tournament.status_id == TournamentStatus.id
        ).join(
            Activity,
            Tournament.activity_id == Activity.id
        ).filter(
            Tournament.organization_id == organization_id,
            TournamentStatus.code == 'completed'
        ).order_by(Tournament.end_date.desc()).all()

        # Convertir a DTOs
        def to_event_dto(event: Event) -> EventDTO:
            return EventDTO(
                id=event.id,
                name=event.name,
                description=event.description[:100] + '...' if event.description and len(event.description) > 100 else event.description or '',
                start_date=event.start_date.strftime('%Y-%m-%d'),
                end_date=event.end_date.strftime('%Y-%m-%d'),
                status=event.status.code
            )

        def to_tournament_dto(tournament: Tournament) -> TournamentDTO:
            return TournamentDTO(
                id=tournament.id,
                name=tournament.name,
                activity_name=tournament.activity.name,
                start_date=tournament.start_date.strftime('%Y-%m-%d %H:%M') if tournament.start_date else 'N/A',
                end_date=tournament.end_date.strftime('%Y-%m-%d %H:%M') if tournament.end_date else 'N/A',
                status=tournament.status.code,
                team_count=len(tournament.teams)
            )

        # Verificar si el usuario es organizador
        is_organizer = OrganizationMember.query.filter_by(
            organization_id=organization_id,
            user_id=user_id,
            is_organizer=True
        ).count() > 0

        return OrganizationDetailDTO(
            id=org.id,
            name=org.name,
            description=org.description,
            created_at=org.created_at.strftime('%Y-%m-%d'),
            creator_name=org.creator.name,
            member_count=len(org.members),
            active_events=[to_event_dto(e) for e in active_events],
            active_tournaments=[to_tournament_dto(t) for t in active_tournaments],
            past_tournaments=[to_tournament_dto(t) for t in past_tournaments],
            is_organizer=is_organizer
        )

    """ Unirse a una organización """
    @staticmethod
    def join_organization(user_id: int, org_id: int) -> tuple[bool, str]:
        """
        Intenta unir al usuario a una organización
        Retorna: (success: bool, message: str)
        """
        from flaskapp.database.models import db, Organization, OrganizationMember
        
        # Verificar si el usuario ya es miembro
        existing_membership = OrganizationMember.query.filter_by(
            user_id=user_id,
            organization_id=org_id
        ).first()
        
        if existing_membership:
            return False, "Ya eres miembro de esta organización"
        
        # Verificar si la organización existe
        organization = Organization.query.get(org_id)
        if not organization:
            return False, "Organización no encontrada"
        
        # Verificar si es admin de plataforma (no necesita unirse)
        user = User.query.get(user_id)
        if user.is_admin:
            return False, "Los administradores no necesitan unirse a organizaciones"
        
        try:
            # Crear nueva membresía
            new_member = OrganizationMember(
                organization_id=org_id,
                user_id=user_id,
                is_organizer=False  # Por defecto no es organizador
            )
            
            db.session.add(new_member)
            db.session.commit()
            
            return True, f"Te has unido exitosamente a {organization.name}"
        
        except Exception as e:
            db.session.rollback()
            return False, f"Error al unirse a la organización: {str(e)}"
        
    """ Crear o editar una organización """
    @staticmethod
    def create_or_update_organization(form_data, organization_id=None, creator_id=None):
        if organization_id:
            # Modo edición
            org = Organization.query.get_or_404(organization_id)
            org.name = form_data['name']
            org.description = form_data['description']
        else:
            # Modo creación
            org = Organization(
                name=form_data['name'],
                description=form_data['description'],
                created_by=creator_id
            )
            db.session.add(org)
        
        db.session.commit()
        return org
    
    @staticmethod
    def get_organization_members(organization_id: int, search: str = None) -> List[MemberDTO]:
        query = db.session.query(
            OrganizationMember,
            User
        ).join(
            User,
            OrganizationMember.user_id == User.id
        ).filter(
            OrganizationMember.organization_id == organization_id,
            User.is_admin == False  # Excluir admins de plataforma
        )
        
        if search:
            query = query.filter(
                db.or_(
                    User.name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        return [
            MemberDTO(
                id=member.id,
                user_id=user.id,
                name=user.name,
                email=user.email,
                is_organizer=member.is_organizer,
                is_admin=user.is_admin
            )
            for member, user in query.all()
        ]

    @staticmethod
    def toggle_organizer(member_id: int, organization_id: int):
        member = OrganizationMember.query.filter_by(
            id=member_id,
            organization_id=organization_id
        ).first_or_404()
        
        if member.user.is_admin:
            raise ValueError("Los administradores no pueden ser organizadores")
        
        member.is_organizer = not member.is_organizer
        db.session.commit()
        return member