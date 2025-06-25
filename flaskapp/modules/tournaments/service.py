import math
from sqlalchemy import and_
from typing import Any, Tuple
from sqlalchemy.orm import aliased
from flask_login import current_user
from flaskapp.database.models import Match, MatchStatus, TeamInvitationStatus, TournamentStatus, db, OrganizationMember, Team, TeamMember, Tournament, TournamentReferee, User, TeamInvitation, Team
from flaskapp.modules.teams.service import TeamService
from flaskapp.modules.tournaments.dto import EligibleRefereeDTO, MatchDTO, MatchTeamDTO, TeamDTO, TeamMemberDTO, TournamentDTO, TournamentDetailDTO
from typing import Dict, List

class TournamentGenerator:
    """
    Genera brackets de torneo de eliminación simple con cabezas de serie y byes.
    TODA la lógica opera con diccionarios de Python para mantenerse desacoplada de la BD.
    """
    
    @staticmethod
    def _calculate_bracket_size(team_count: int) -> Tuple[int, int]:
        """Calcula el tamaño del bracket y el número de byes necesarios."""
        if team_count < 2:
            raise ValueError("Se requieren al menos dos equipos para un torneo.")
        
        bracket_size = 2 ** math.ceil(math.log2(team_count))
        byes_count = bracket_size - team_count
        return bracket_size, byes_count

    @staticmethod
    def _seed_teams(teams: List['Team']) -> List['Team']:
        """Ordena los equipos por seed_score (los mejores primero)."""
        return sorted(teams, key=lambda x: x.seed_score, reverse=True)

    @staticmethod
    def _create_initial_matches(
        sorted_teams: List['Team'],
        level: int,
        byes_count: int,
        pending_status_id: int,
        completed_status_id: int
    ) -> List[Dict[str, Any]]:
        """
        Crea los diccionarios que representan las partidas iniciales de la primera ronda.
        Maneja tanto partidas regulares como byes.
        """
        matches = []
        
        # Crear partidas de bye (victorias automáticas para los mejores seeds)
        for i in range(byes_count):
            bye_team = sorted_teams[i]
            matches.append({
                "level": level,
                "match_number": 0,  # Temporal, se asignará correctamente después
                "team_a_id": bye_team.id,
                "team_b_id": None,
                "is_bye": True,
                "status_id": 2,
                "winner_id": bye_team.id
            })
        
        # Crear partidas regulares para los equipos restantes
        remaining_teams = sorted_teams[byes_count:]
        for i in range(0, len(remaining_teams), 2):
            team_a = remaining_teams[i]
            team_b = remaining_teams[i + 1] if i + 1 < len(remaining_teams) else None
            
            matches.append({
                "level": level,
                "match_number": 0,  # Temporal
                "team_a_id": team_a.id,
                "team_b_id": team_b.id if team_b else None,
                "is_bye": False,
                "status_id": pending_status_id
            })
            
        return matches

    @staticmethod
    def _assign_match_numbers(matches: List[Dict[str, Any]], level: int) -> List[Dict[str, Any]]:
        """
        Asigna los números de partida correctos siguiendo los patrones de seeding del torneo.
        """
        if not matches:
            return []
            
        num_matches_in_level = len(matches)
        base_match_number = 2**level
        
        # Standard Seeding Order (e.g., for 8 slots: 1 vs 8, 4 vs 5, 2 vs 7, 3 vs 6)
        # This simplified assignment ensures unique numbers per level.
        # A more complex algorithm could be used for precise bracket placement.
        for i, match in enumerate(matches):
            match['match_number'] = base_match_number + i

        return sorted(matches, key=lambda m: m['match_number'])

    @staticmethod
    def generate_initial_matches(
        teams: List['Team'], 
        pending_status_id: int, 
        completed_status_id: int
    ) -> List[Dict[str, Any]]:
        """
        Genera una lista de diccionarios para la primera ronda de partidas del torneo.
        """
        if len(teams) < 2:
            raise ValueError("Se necesitan al menos dos equipos para generar partidas.")
            
        sorted_teams = TournamentGenerator._seed_teams(teams)
        bracket_size, byes_count = TournamentGenerator._calculate_bracket_size(len(teams))
        
        # El nivel inicial es el más alto (ej: para 8 equipos, size=8, log2(8)=3, nivel=2)
        level = int(math.log2(bracket_size)) - 1 if bracket_size > 1 else 0

        matches = TournamentGenerator._create_initial_matches(
            sorted_teams, level, byes_count, pending_status_id, completed_status_id
        )
        
        # La asignación de números de partida es crucial para el orden del bracket
        ordered_matches = TournamentGenerator._assign_match_numbers(matches, level)
        
        return ordered_matches

    @staticmethod
    def generate_full_bracket(
        teams: List['Team'], 
        pending_status_id: int, 
        completed_status_id: int
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Genera un bracket completo como un diccionario de niveles, donde cada nivel
        contiene una lista de diccionarios de partidas.
        """
        if len(teams) < 2:
            raise ValueError("Se necesitan al menos 2 equipos para generar un bracket.")

        initial_matches = TournamentGenerator.generate_initial_matches(
            teams, pending_status_id, completed_status_id
        )
        
        bracket_size, _ = TournamentGenerator._calculate_bracket_size(len(teams))
        max_level = int(math.log2(bracket_size)) - 1 if bracket_size > 1 else 0

        matches_by_level = {max_level: initial_matches}

        # Generar niveles superiores (semifinales, final, etc.) vacíos
        for level in range(max_level - 1, -1, -1):
            num_matches_in_level = 2 ** level
            matches_in_level = []

            for i in range(num_matches_in_level):
                # El número de partida en un árbol binario es base + índice
                match_number = (2 ** level) + i
                matches_in_level.append({
                    "level": level,
                    "match_number": match_number,
                    "is_bye": False,
                    "status_id": pending_status_id,
                    "team_a_id": None, # Se llenarán a medida que avance el torneo
                    "team_b_id": None,
                })
            
            matches_by_level[level] = matches_in_level

        return matches_by_level


class TournamentService:

    @staticmethod
    def start_tournament(tournament_id: int) -> bool:
        """
        Inicia un torneo: genera todas las partidas a partir de diccionarios
        y las guarda en la base de datos, actualizando el estado del torneo.
        """
        tournament = Tournament.query.get_or_404(tournament_id)

        # Prueba ejecutar esto justo antes de tu operación fallida
        """
        print(f"Realizando prueba de inserción de partida para el torneo {tournament_id}", flush=True)
        test_match = Match(
            tournament_id=7,
            level=2,
            match_number=99,  # Usa un número que no exista
            team_a_id=18,
            team_b_id=None,
            is_bye=True,
            status_id=2,
            winner_id=18
        )
        db.session.add(test_match)
        db.session.commit()
        print(f"Partida de prueba insertada correctamente para el torneo {tournament_id}", flush=True)
        """

        # 1. Validar el estado actual del torneo
        if tournament.status.code != 'REGISTRATION_OPEN':
            raise ValueError("El torneo debe estar en 'REGISTRATION_OPEN' para poder iniciarse.")

        teams = Team.query.filter_by(tournament_id=tournament_id).all()
        if len(teams) < 2:
            raise ValueError("Se necesitan al menos dos equipos para iniciar el torneo.")

        # 2. Obtener los IDs de estado necesarios ANTES de la generación
        try:
            in_progress_status = db.session.query(TournamentStatus).filter_by(code='IN_PROGRESS').one()
            pending_match_status = db.session.query(MatchStatus).filter_by(code='PENDING').one()
            completed_match_status = db.session.query(MatchStatus).filter_by(code='COMPLETED').one()
        except Exception as e:
            raise RuntimeError(f"No se pudieron encontrar los estados necesarios en la BD: {e}")

        # 3. Generar el bracket como una estructura de datos (diccionarios)
        match_data_by_level = TournamentGenerator.generate_full_bracket(
            teams, pending_match_status.id, completed_match_status.id
        )

        if not match_data_by_level:
            raise ValueError("No se pudieron generar las partidas para el torneo.")
            
        team_map = {team.id: team for team in teams}

        # 4. Convertir los diccionarios a objetos Match y añadirlos a la sesión
        #    *** ESTA ES LA SECCIÓN CORREGIDA ***
        total_matches_created = 0
        for level, match_dicts in match_data_by_level.items():
            for match_data in match_dicts:
                
                # Asignar el ID del torneo que falta en el diccionario
                match_data['tournament_id'] = tournament_id
                
                # --- INICIO DE LA CORRECCIÓN CLAVE ---
                # En lugar de Match(**match_data), creamos una instancia vacía
                # y asignamos los atributos manualmente. Esto evita problemas
                # con un posible constructor __init__ personalizado en el modelo Match.
                new_match = Match()
                for key, value in match_data.items():
                    setattr(new_match, key, value)
                # --- FIN DE LA CORRECCIÓN CLAVE ---
                
                # Logging para depuración (opcional pero útil)
                team_a_name = team_map.get(new_match.team_a_id).name if new_match.team_a_id else "TBD"
                team_b_name = "BYE" if new_match.is_bye else (team_map.get(new_match.team_b_id).name if new_match.team_b_id else "TBD")
                print(f"  Añadiendo a la sesión: Match {new_match.match_number} ({team_a_name} vs {team_b_name}) con StatusID: {new_match.status_id}", flush=True)

                db.session.add(new_match)
                total_matches_created += 1

        print(f"Total de partidas para añadir a la sesión: {total_matches_created}", flush=True)

        # 5. Actualizar el estado del torneo a 'IN_PROGRESS'
        print(f"Actualizando estado del torneo '{tournament.name}' a IN_PROGRESS (ID: {in_progress_status.id})", flush=True)
        tournament.status_id = in_progress_status.id
        
        try:
            # Confirmar todos los cambios en la base de datos en una sola transacción
            db.session.commit()
            print(f"Torneo '{tournament.name}' iniciado exitosamente.", flush=True)
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: No se pudo iniciar el torneo '{tournament.name}'. Rollback ejecutado. Causa: {e}", flush=True)
            # Levantar el error original es más informativo para el debugging
            raise e

        return True

    @classmethod
    def cancel_tournament(cls, tournament_id):
        # Obtener el estado "CANCELLED" de la base de datos
        cancelled_status = db.session.query(TournamentStatus).filter_by(code='CANCELLED').one()
        print(f"Estado de torneo cancelado: {cancelled_status.code}", flush=True)
        
        # Obtener el torneo
        tournament = db.session.query(Tournament).get(tournament_id)
        if not tournament:
            raise ValueError("Torneo no encontrado")
        
        # Verificar que el torneo no esté ya completado o cancelado
        if tournament.status.code in ['COMPLETED', 'CANCELLED']:
            raise ValueError("No se puede cancelar un torneo que ya está completado o cancelado")
        
        # Actualizar el estado
        tournament.status_id = cancelled_status.id
        
        # Opcional: cancelar también todos los partidos pendientes
        matches = db.session.query(Match).filter_by(tournament_id=tournament_id).all()
        cancelled_match_status = db.session.query(MatchStatus).filter_by(code='CANCELLED').one()
        
        for match in matches:
            if match.status.code == 'PENDING':
                match.status_id = cancelled_match_status.id
        
        db.session.commit()

    @staticmethod
    def get_team_initation_status_id(code: str) -> int:
        return db.session.query(TeamInvitationStatus.id).filter_by(code=code).scalar()

    @staticmethod
    def get_user_pending_invitations(tournament_id, user_id):
        """Obtiene todas las invitaciones pendientes de un usuario para un torneo específico"""

        pending_status_id = db.session.query(TeamInvitationStatus.id).filter_by(code='PENDING').scalar()

        return TeamInvitation.query.join(
            Team, Team.id == TeamInvitation.team_id
        ).filter(
            Team.tournament_id == tournament_id,
            TeamInvitation.invited_user_id == user_id,
            TeamInvitation.status_id == pending_status_id
        ).all()

    @staticmethod
    def reject_invitation(invitation_id, user_id):
        pending_status_id = TournamentService.get_team_initation_status_id('PENDING')
        rejected_status_id = TournamentService.get_team_initation_status_id('REJECTED')

        invitation = TeamInvitation.query.filter(
            TeamInvitation.id == invitation_id,
            TeamInvitation.invited_user_id == user_id,
            TeamInvitation.status_id == pending_status_id
        ).first_or_404()

        try:
            invitation.status_id = rejected_status_id
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e


    @staticmethod
    def accept_invitation(invitation_id, user_id):
        """Acepta una invitación y rechaza las demás"""
        pending_status_id = TournamentService.get_team_initation_status_id('PENDING')
        accepted_status_id = TournamentService.get_team_initation_status_id('ACCEPTED')
        rejected_status_id = TournamentService.get_team_initation_status_id('REJECTED')

        invitation = TeamInvitation.query.filter_by(
            id=invitation_id,
            invited_user_id=user_id,
            status_id=pending_status_id
        ).first_or_404()

        # Verificar que el usuario no esté ya en otro equipo del torneo
        existing_membership = TeamMember.query.join(
            Team, Team.id == TeamMember.team_id
        ).filter(
            Team.tournament_id == invitation.team.tournament_id,
            TeamMember.user_id == user_id
        ).first()

        if existing_membership:
            raise ValueError("Ya eres miembro de otro equipo en este torneo")

        # Verificar que el usuario no sea árbitro del torneo
        if any(ref.user_id == user_id for ref in invitation.team.tournament.referees):
            raise ValueError("Los árbitros no pueden unirse a equipos")

        try:
            # Aceptar esta invitación
            invitation.status_id = accepted_status_id

            # Rechazar todas las demás pendientes
            invitations = TeamInvitation.query.join(
                Team, Team.id == TeamInvitation.team_id
            ).filter(
                Team.tournament_id == invitation.team.tournament_id,
                TeamInvitation.invited_user_id == user_id,
                TeamInvitation.status_id == pending_status_id,
                TeamInvitation.id != invitation.id
            ).all()

            for inv in invitations:
                inv.status_id = rejected_status_id


            # Agregar usuario como miembro del equipo
            db.session.add(TeamMember(
                team_id=invitation.team_id,
                user_id=user_id,
                is_leader=False
            ))

            # Calcular el nuevo seed_score con TODOS los miembros (incluyendo el nuevo)
            team = Team.query.get(invitation.team_id)
            team.seed_score = TeamService.calculate_team_seed(team.id)

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e


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
    
    @staticmethod
    def get_tournament_matches(tournament_id: int) -> List[MatchDTO]:
        """Obtiene todos los matches de un torneo con su información relevante"""
        matches = Match.query.filter_by(tournament_id=tournament_id)\
            .options(
                db.joinedload(Match.team_a),
                db.joinedload(Match.team_b),
                db.joinedload(Match.status)
            )\
            .order_by(Match.level.desc(), Match.match_number.asc())\
            .all()

        result = []
        for match in matches:
            team_a_dto = MatchTeamDTO(
                id=match.team_a.id,
                name=match.team_a.name,
                seed_score=match.team_a.seed_score
            ) if match.team_a else None

            team_b_dto = MatchTeamDTO(
                id=match.team_b.id,
                name=match.team_b.name,
                seed_score=match.team_b.seed_score
            ) if match.team_b else None

            result.append(MatchDTO(
                id=match.id,
                level=match.level,
                match_number=match.match_number,
                team_a=team_a_dto,
                team_b=team_b_dto,
                score_team_a=match.score_team_a,
                score_team_b=match.score_team_b,
                winner_id=match.winner_id,
                status=match.status.code,
                is_bye=match.is_bye,
                completed_at=match.completed_at.isoformat() if match.completed_at else None
            ))
        
        return result