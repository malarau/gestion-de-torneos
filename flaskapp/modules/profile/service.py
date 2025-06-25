from flask import abort
from sqlalchemy import func, or_
from flaskapp.database.models import Activity, Match, MatchStatus, Organization, Team, TeamMember, Tournament, TournamentReferee, TournamentStatus, User
from flaskapp.modules.profile.dto import TournamentStats, UserProfileDTO, UserStats

from flaskapp.database.models import OrganizationMember, db

class ProfileService:
    @staticmethod
    def get_user_profile(user_id: int, current_user_id: int) -> UserProfileDTO:
        user = User.query.get_or_404(user_id)
        
        common_orgs = []
        if user_id != current_user_id:
            # Obtener organizaciones en común
            common_orgs = db.session.query(
                Organization.id,
                Organization.name,
                OrganizationMember.is_organizer
            ).join(
                OrganizationMember,
                Organization.id == OrganizationMember.organization_id
            ).filter(
                OrganizationMember.user_id == current_user_id,
                Organization.id.in_(
                    db.session.query(OrganizationMember.organization_id)
                    .filter(OrganizationMember.user_id == user_id)
                )
            ).all()
            
            if not common_orgs:
                abort(403)

        return UserProfileDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_picture=user.profile_picture or '/static/assets/img/theme/default-profile.png',
            created_at=user.created_at.strftime('%d. %B %Y'),
            is_current_user=(user_id == current_user_id),
            common_organizations=[{
                'id': org.id,
                'name': org.name,
                'is_organizer': org.is_organizer
            } for org in common_orgs]
        )

    @staticmethod
    def update_profile(user_id: int, form_data: dict):
        user = User.query.get_or_404(user_id)
        user.name = form_data['name']
        db.session.commit()
        return user

    def get_user_stats(user_id):        
        stats = UserStats()
        
        # Torneos jugados (como miembro de equipo)
        stats.tournaments_played = db.session.query(Tournament).join(
            Team, Team.tournament_id == Tournament.id
        ).join(
            TeamMember, TeamMember.team_id == Team.id
        ).filter(
            TeamMember.user_id == user_id
        ).count()
        
        # Partidos ganados y perdidos
        matches_won = db.session.query(Match).join(
            Team, Team.id == Match.winner_id
        ).join(
            TeamMember, TeamMember.team_id == Team.id
        ).filter(
            TeamMember.user_id == user_id,
            Match.winner_id.isnot(None)
        ).count()
        
        matches_participated = db.session.query(Match).join(
            Team, or_(Team.id == Match.team_a_id, Team.id == Match.team_b_id)
        ).join(
            TeamMember, TeamMember.team_id == Team.id
        ).filter(
            TeamMember.user_id == user_id,
            Match.status_id == MatchStatus.query.filter_by(code='COMPLETED').first().id
        ).count()
        
        stats.matches_won = matches_won
        stats.matches_lost = matches_participated - matches_won
        stats.win_rate = round((matches_won / matches_participated * 100) if matches_participated > 0 else 0, 1)
        
        # Actividad favorita
        favorite_activity = db.session.query(
            Activity.name,
            func.count(Tournament.id).label('count')
        ).join(
            Tournament, Tournament.activity_id == Activity.id
        ).join(
            Team, Team.tournament_id == Tournament.id
        ).join(
            TeamMember, TeamMember.team_id == Team.id
        ).filter(
            TeamMember.user_id == user_id
        ).group_by(
            Activity.name
        ).order_by(
            func.count(Tournament.id).desc()
        ).first()
        
        if favorite_activity:
            stats.favorite_activity = favorite_activity[0]
            stats.favorite_activity_count = favorite_activity[1]
        
        # Veces como árbitro
        stats.referee_count = TournamentReferee.query.filter_by(user_id=user_id).count()
        
        # Equipos liderados
        stats.leader_count = TeamMember.query.filter_by(
            user_id=user_id, is_leader=True
        ).count()
        
        # Últimos torneos participados
        recent_tournaments = db.session.query(
            Tournament.id,
            Tournament.name,
            Organization.name.label('organization_name'),
            Organization.id.label('organization_id'),
            TournamentStatus.code.label('status'),
            TournamentStatus.description.label('status_display')
        ).join(
            Organization, Organization.id == Tournament.organization_id
        ).join(
            Team, Team.tournament_id == Tournament.id
        ).join(
            TeamMember, TeamMember.team_id == Team.id
        ).join(
            TournamentStatus, TournamentStatus.id == Tournament.status_id
        ).filter(
            TeamMember.user_id == user_id
        ).order_by(
            Tournament.start_date.desc()
        ).limit(5).all()
        
        stats.recent_tournaments = [
            TournamentStats(
                id=t.id,
                name=t.name,
                organization_name=t.organization_name,
                organization_id=t.organization_id,
                status=t.status,
                status_display=t.status_display
            ) for t in recent_tournaments
        ]
        
        return stats