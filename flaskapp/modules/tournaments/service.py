from sqlalchemy import and_
from sqlalchemy.orm import aliased
from flask_login import current_user
from flaskapp.database.models import db, OrganizationMember, Team, TeamMember, Tournament, TournamentReferee, User
from flaskapp.modules.tournaments.dto import EligibleRefereeDTO, TeamDTO, TeamMemberDTO, TournamentDTO, TournamentDetailDTO
from typing import List

class TournamentService:

    @staticmethod
    def can_create_team(tournament_id: int, user_id: int = None) -> bool:
        """
        Determina si un usuario puede crear un equipo en el torneo.
        """
        if user_id is None:
            if not current_user.is_authenticated:
                return False
            user_id = current_user.id
        
        tournament = Tournament.query.get_or_404(tournament_id)
        
        # 1. No puede si es admin de plataforma
        user = User.query.get(user_id)
        if user.is_admin:
            return False
            
        # 2. No puede si es organizador de la organización
        is_organizer = OrganizationMember.query.filter(
            and_(
                OrganizationMember.organization_id == tournament.organization_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_organizer == True
            )
        ).first() is not None
        
        if is_organizer:
            return False
            
        # 3. No puede si ya tiene equipo en el torneo
        has_team = TeamMember.query.join(
            Team
        ).filter(
            and_(
                Team.tournament_id == tournament_id,
                TeamMember.user_id == user_id
            )
        ).first() is not None
        
        if has_team:
            return False
            
        # 4. No puede si es árbitro del torneo
        is_referee = TournamentReferee.query.filter(
            and_(
                TournamentReferee.tournament_id == tournament_id,
                TournamentReferee.user_id == user_id
            )
        ).first() is not None
        
        if is_referee:
            return False
            
        # 6. Verificar que el torneo esté en fase de registro
        if tournament.status.code != 'REGISTRATION_OPEN':
            return False
            
        return True

    @staticmethod
    def create_or_update_tournament(form, organization_id, tournament_id=None):
        """Create or update a tournament based on form data"""
        if tournament_id:
            tournament = Tournament.query.get_or_404(tournament_id)
            if tournament.organization_id != organization_id:
                raise ValueError("No tienes permiso para editar este torneo")
        else:
            tournament = Tournament(organization_id=organization_id)

        # Verificar permisos del organizador
        is_organizer = OrganizationMember.query.filter_by(
            organization_id=organization_id,
            user_id=current_user.id,
            is_organizer=True
        ).first() is not None

        if not is_organizer:
            raise ValueError("Solo los organizadores pueden crear o editar torneos")

        # Actualizar campos del torneo
        tournament.name = form.name.data
        tournament.description = form.description.data
        tournament.activity_id = form.activity_id.data
        tournament.max_teams = form.max_teams.data
        tournament.start_date = form.start_date.data
        tournament.end_date = form.end_date.data
        tournament.prizes = form.prizes.data
        tournament.status_id = form.status_id.data
        tournament.event_id = form.event_id.data if form.event_id.data != -1 else None
        tournament.created_by = current_user.id

        if not tournament_id:
            db.session.add(tournament)
        
        db.session.commit()
        return tournament
    
    @staticmethod
    def get_organization_tournaments(organization_id: int, user_id: int) -> List[TournamentDTO]:
        tournaments = Tournament.query.filter_by(
            organization_id=organization_id
        ).options(
            db.joinedload(Tournament.activity),
            db.joinedload(Tournament.status),
            db.joinedload(Tournament.teams)
        ).all()

        is_organizer = OrganizationMember.query.filter_by(
            organization_id=organization_id,
            user_id=user_id,
            is_organizer=True
        ).first() is not None

        return [
            TournamentDTO(
                id=t.id,
                name=t.name,
                activity_name=t.activity.name,
                start_date=t.start_date.strftime('%Y-%m-%d %H:%M') if t.start_date else 'N/A',
                end_date=t.end_date.strftime('%Y-%m-%d %H:%M') if t.end_date else 'N/A',
                status=t.status.code,
                max_teams=t.max_teams,
                team_count=len(t.teams),
                can_edit=is_organizer,
                is_team_creation_open=t.status.code == 'REGISTRATION_OPEN'  # Calculado basado en estado
            ) for t in tournaments
        ]

    @staticmethod
    def get_tournament_detail(tournament_id: int, user_id: int) -> TournamentDetailDTO:
        # Consulta principal con todas las relaciones necesarias
        tournament = Tournament.query.options(
            db.joinedload(Tournament.activity),
            db.joinedload(Tournament.status),
            db.joinedload(Tournament.creator),
            db.joinedload(Tournament.organization),
            db.joinedload(Tournament.event),
            db.joinedload(Tournament.referees).joinedload(TournamentReferee.user),
            db.joinedload(Tournament.teams).subqueryload(Team.members).joinedload(TeamMember.user)
        ).get_or_404(tournament_id)

        # Verificar si el usuario es organizador
        is_organizer = db.session.query(
            OrganizationMember.query.filter_by(
                organization_id=tournament.organization_id,
                user_id=user_id,
                is_organizer=True
            ).exists()
        ).scalar()

        # Obtener equipos con sus miembros de manera optimizada
        teams_data = []
        for team in tournament.teams:
            members = []
            for member in team.members:
                members.append(TeamMemberDTO(
                    user_id=member.user.id,
                    name=member.user.name,
                    email=member.user.email,
                    profile_picture=member.user.profile_picture or '/static/assets/img/theme/team-1.jpg',
                    is_leader=member.is_leader
                ))
            
            teams_data.append(TeamDTO(
                id=team.id,
                name=team.name,
                seed_score=team.seed_score,
                members=members
            ))

        # Verificar si el usuario tiene un equipo en este torneo
        user_has_team = db.session.query(TeamMember).select_from(TeamMember).join(Team).filter(
            TeamMember.user_id == user_id,
            Team.tournament_id == tournament_id
        ).first() is not None

        return TournamentDetailDTO(
            id=tournament.id,
            name=tournament.name,
            activity_name=tournament.activity.name,
            activity_id=tournament.activity_id,
            start_date=tournament.start_date.strftime('%Y-%m-%d %H:%M') if tournament.start_date else 'N/A',
            end_date=tournament.end_date.strftime('%Y-%m-%d %H:%M') if tournament.end_date else 'N/A',
            status=tournament.status.code,
            status_id=tournament.status_id,
            max_teams=tournament.max_teams,
            team_count=len(tournament.teams),
            can_edit=is_organizer,
            is_team_creation_open=tournament.status.code == 'REGISTRATION_OPEN',
            description=tournament.description,
            prizes=tournament.prizes,
            created_by=tournament.creator.name if tournament.creator else 'Sistema',
            created_at=tournament.created_at.strftime('%Y-%m-%d'),
            updated_at=tournament.updated_at.strftime('%Y-%m-%d') if tournament.updated_at else '',
            referees=[{
                'user_id': r.user.id,
                'id': r.id,
                'name': r.user.name,
                'email': r.user.email,
                'profile_picture': r.user.profile_picture
            } for r in tournament.referees],
            organization_name=tournament.organization.name,
            event_name=tournament.event.name if tournament.event else None,
            event_id=tournament.event_id if tournament.event else None,
            teams=teams_data,
            user_has_team=user_has_team
        )

    @staticmethod
    def get_eligible_referees(tournament_id: int, search: str = None) -> List[EligibleRefereeDTO]:
        tournament = Tournament.query.get_or_404(tournament_id)
        
        # Subquery para miembros que ya son árbitros
        existing_referees = db.session.query(TournamentReferee.user_id).filter_by(
            tournament_id=tournament_id
        )
        existing_referee_ids = [ref_id for (ref_id,) in existing_referees]        

        # Subquery para miembros que están en equipos
        team_members = db.session.query(TeamMember.user_id).join(
            Team
        ).filter(
            Team.tournament_id == tournament_id
        )
        
        query = db.session.query(
            OrganizationMember,
            User
        ).join(
            User,
            OrganizationMember.user_id == User.id
        ).filter(
            OrganizationMember.organization_id == tournament.organization_id,
            User.is_admin == False,
            OrganizationMember.is_organizer == False,
            OrganizationMember.user_id.notin_(team_members)
        )
        
        if search:
            query = query.filter(
                db.or_(
                    User.name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )

        results = query.all()

        return [
            EligibleRefereeDTO(
                id=member.id,
                user_id=user.id,
                name=user.name,
                email=user.email,
                is_referee=user.id in existing_referee_ids,
                profile_picture=user.profile_picture
            ) for member, user in results
        ]

    @staticmethod
    def toggle_referee(tournament_id: int, user_id: int):
        tournament = Tournament.query.get_or_404(tournament_id)

        # Verificar si ya es árbitro
        existing = TournamentReferee.query.filter_by(
            tournament_id=tournament_id,
            user_id=user_id
        ).first()

        if existing:
            db.session.delete(existing)
            db.session.commit()
            return 'removed'

        # Subconsulta: si el usuario está en un equipo de este torneo
        team_alias = aliased(Team)


        user_in_tournament_team = db.session.query(TeamMember.id).join(
            team_alias, TeamMember.team_id == team_alias.id
        ).filter(
            TeamMember.user_id == user_id,
            team_alias.tournament_id == tournament_id
        ).exists()

        # Verificar elegibilidad si NO está en un equipo del torneo
        eligible = db.session.query(
            OrganizationMember
        ).join(User).filter(
            OrganizationMember.organization_id == tournament.organization_id,
            OrganizationMember.user_id == user_id,
            User.is_admin == False,
            OrganizationMember.is_organizer == False,
            ~user_in_tournament_team
        ).first()

        if not eligible:
            raise ValueError("El usuario no cumple los requisitos para ser árbitro")

        new_referee = TournamentReferee(
            tournament_id=tournament_id,
            user_id=user_id,
            assigned_by=current_user.id
        )
        db.session.add(new_referee)
        db.session.commit()
        return 'added'