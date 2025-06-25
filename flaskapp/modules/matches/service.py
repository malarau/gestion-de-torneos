from datetime import datetime
import math
from typing import Optional
from flaskapp.database.models import MatchStatus, Tournament, db
from flaskapp.database.models import Match, Team, TournamentReferee, User
from flaskapp.modules.matches.dto import MatchDTO
from sqlalchemy.orm import joinedload

class MatchService:
    @staticmethod
    @staticmethod
    def is_user_tournament_referee(user_id: int, tournament_id: int) -> bool:
        """Verifica si un usuario es árbitro en un torneo específico"""
        return db.session.query(
            TournamentReferee.query.filter_by(
                tournament_id=tournament_id,
                user_id=user_id
            ).exists()
        ).scalar()

    @staticmethod
    def get_match_details(match_id: int) -> Optional[MatchDTO]:
        match = Match.query.options(
            joinedload(Match.team_a),
            joinedload(Match.team_b),
            joinedload(Match.best_player),
            joinedload(Match.recorded_by_referee) # Asumiendo que tienes una relación definida en el modelo
        ).get(match_id)
        if not match:
            return None

        # Obtener información de equipos
        team_a = Team.query.get(match.team_a_id) if match.team_a_id else None
        team_b = Team.query.get(match.team_b_id) if match.team_b_id else None
        
        # Obtener líderes de equipo
        def get_team_leader_info(team):
            if team:
                leader = next((m.user for m in team.members if m.is_leader), None)
                if leader:
                    return {
                        'name': f"{leader.name}",
                        'id': leader.id,
                        'pic': leader.profile_picture
                    }
            return {'name': None, 'id': None, 'pic': None}

        team_a_info = get_team_leader_info(team_a)
        team_b_info = get_team_leader_info(team_b)
        
        # Obtener mejor jugador
        best_player = User.query.get(match.best_player_id) if match.best_player_id else None
        best_player_info = {
            'name': f"{best_player.name}" if best_player else None,
            'id': match.best_player_id,
            'pic': best_player.profile_picture if best_player else None
        }
        
        # Obtener árbitro
        referee = User.query.get(match.recorded_by_referee_id) if match.recorded_by_referee_id else None
        referee_info = {
            'name': f"{referee.name}" if referee else None,
            'id': match.recorded_by_referee_id
        }

        return MatchDTO(
            id=match.id,
            tournament_id=match.tournament_id,
            level=match.level,
            match_number=match.match_number,
            team_a_id=match.team_a_id,
            team_b_id=match.team_b_id,
            team_a_members=team_a.members if team_a else [],
            team_b_members=team_b.members if team_b else [],
            team_a_name=team_a.name if team_a else None,
            team_b_name=team_b.name if team_b else None,
            team_a_score=match.score_team_a,
            team_b_score=match.score_team_b,
            winner_id=match.winner_id,
            best_player_id=match.best_player_id,
            best_player_name=best_player_info['name'],
            best_player_pic=best_player_info['pic'],
            is_bye=match.is_bye,
            status=match.status.code,
            status_description=match.status.description,
            completed_at=match.completed_at,
            recorded_by_referee_id=referee_info['id'],
            recorded_by_referee_name=referee_info['name'],
            team_a_leader=team_a_info,
            team_b_leader=team_b_info
        )

    @staticmethod
    def get_eligible_players(match_id: int) -> list:
        """Obtiene jugadores elegibles como MVP (de ambos equipos)"""
        match = Match.query.get(match_id)
        if not match:
            return []

        players = []
        for team_id in [match.team_a_id, match.team_b_id]:
            if team_id:
                team = Team.query.get(team_id)
                players.extend([
                    {
                        'id': member.user.id,
                        'name': f"{member.user.name}",
                        'team': team.name
                    }
                    for member in team.members
                ])
        return players
    
    @staticmethod
    def can_edit_match(match_id: int, user_id: int) -> bool:
        """Verifica si el partido puede ser editado por el usuario"""
        match = Match.query.get(match_id)
        if not match:
            return False
        
        # 0. Verificar que la partida cuente con 2 equipos y no sea un bye
        # Si no tiene equipos asignados o es un bye, no se puede editar
        if not match.team_a_id or not match.team_b_id or match.is_bye:
            return False

        # 1. Verificar si el usuario es árbitro del torneo
        if not MatchService.is_user_tournament_referee(user_id, match.tournament_id):
            return False

        # 2. Verificar estado del torneo
        tournament = Tournament.query.get(match.tournament_id)
        if tournament.status.code != 'IN_PROGRESS':
            return False
        
        # 3. Verificar estado del partido (no es CANCELLED)
        if match.status.code == 'CANCELLED':
            return False

        # 4. Verificar siguiente partido en el bracket
        next_match_number = match.match_number // 2
        if next_match_number > 0:
            next_match = Match.query.filter_by(
                tournament_id=match.tournament_id,
                match_number=next_match_number
            ).first()
            
            if next_match and next_match.status.code == 'COMPLETED':
                return False

        return True

    @staticmethod
    def update_match(match_id: int, update_data: dict) -> bool:
        """Actualiza un partido, determina ganador y propaga al siguiente si corresponde"""
        if not MatchService.can_edit_match(match_id, update_data.get('user_id')):
            return False

        match = Match.query.get(match_id)
        if not match:
            return False

        try:
            match.score_team_a = update_data.get('score_team_a')
            match.score_team_b = update_data.get('score_team_b')
            match.best_player_id = update_data.get('best_player_id')
            match.recorded_by_referee_id = update_data.get('recorded_by_referee_id')

            # Obtener ID de estado 'COMPLETED'
            completed_status = MatchStatus.query.filter_by(code='COMPLETED').first()
            if not completed_status:
                raise ValueError("Estado 'COMPLETED' no encontrado")

            # Si ambos scores están presentes, marcar como completado
            if match.score_team_a is not None and match.score_team_b is not None:
                print(f"Marcando match {match.id} como completado", flush=True)
                match.status_id = completed_status.id
                match.completed_at = datetime.utcnow()

                # Determinar ganador
                if match.score_team_a > match.score_team_b:
                    match.winner_id = match.team_a_id
                elif match.score_team_b > match.score_team_a:
                    match.winner_id = match.team_b_id
                else:
                    # Empates no permitidos
                    raise ValueError("No se permiten empates")

                # Propagación al siguiente match (si no es final)
                if match.level > 0 and match.winner_id:
                    print(f"Actualizando siguiente partido para el match {match.id} (Nivel {match.level}, Match {match.match_number})", flush=True)
                    next_match_number = match.match_number // 2
                    next_level = match.level - 1

                    next_match = Match.query.filter_by(
                        tournament_id=match.tournament_id,
                        level=next_level,
                        match_number=next_match_number
                    ).first()

                    if next_match:
                        print(f"Actualizando siguiente partido: {next_match.id} (Nivel {next_level}, Match {next_match_number})", flush=True)
                        if match.match_number % 2 == 0:
                            # par → posición izquierda (team_a)
                            next_match.team_a_id = match.winner_id
                        else:
                            # impar → posición derecha (team_b)
                            next_match.team_b_id = match.winner_id
                    else:
                        print(f"No se encontró el siguiente partido para el match {match.id} (Nivel {next_level}, Match {next_match_number})", flush=True)
                else:
                    print(f"Match {match.id} es final o no tiene ganador, no se propaga al siguiente match", flush=True)
            else:
                print(f"Match {match.id} no está completo, no se actualiza estado ni ganador", flush=True)

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error actualizando match: {e}")
            return False
