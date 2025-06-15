from datetime import datetime, timedelta
from sqlalchemy import and_
from flaskapp.database.models import db, User, Organization, Tournament, Team
from flaskapp.modules.home.dto import DashboardStatsDTO
from flaskapp.modules.home.utils import TimeLabelGenerator

class DashboardService:
    @staticmethod
    def get_dashboard_stats():
        # Totales actuales
        total_users = User.query.count()
        total_organizations = Organization.query.count()
        total_tournaments = Tournament.query.count()
        total_teams = Team.query.count()

        # Fechas para cálculos de variación
        now = datetime.utcnow()
        one_month_ago = now - timedelta(days=30)
        
        # Cálculo de variaciones porcentuales
        def calculate_change_percentage(current_count, previous_count):
            if previous_count == 0:
                if current_count == 0:
                    return 0.0
                return 100.0  # Si no había registros previos, consideramos crecimiento del 100%
            return ((current_count - previous_count) / previous_count) * 100

        # Usuarios
        users_month_ago = User.query.filter(User.created_at <= one_month_ago).count()
        users_change = calculate_change_percentage(total_users, users_month_ago)

        # Organizaciones
        orgs_month_ago = Organization.query.filter(Organization.created_at <= one_month_ago).count()
        orgs_change = calculate_change_percentage(total_organizations, orgs_month_ago)

        # Torneos
        tournaments_month_ago = Tournament.query.filter(Tournament.created_at <= one_month_ago).count()
        tournaments_change = calculate_change_percentage(total_tournaments, tournaments_month_ago)

        # Equipos
        teams_month_ago = Team.query.filter(Team.created_at <= one_month_ago).count()
        teams_change = calculate_change_percentage(total_teams, teams_month_ago)

        # Usuarios últimos 6 meses
        users_last_6_months = []
        for i in range(5, -1, -1):  # Desde hace 5 meses hasta el mes actual
            month_start = now.replace(day=1) - timedelta(days=30*i)
            next_month_start = month_start + timedelta(days=32)
            next_month_start = next_month_start.replace(day=1)
            
            users_in_month = User.query.filter(
                and_(
                    User.created_at >= month_start,
                    User.created_at < next_month_start
                )
            ).count()
            users_last_6_months.append(users_in_month)

        # Últimos 6 meses como etiquetas
        label_generator = TimeLabelGenerator()
        last_6_months = label_generator.get_last_month_labels()    

        return DashboardStatsDTO(
            total_users=total_users,
            users_change_percentage=users_change,
            total_organizations=total_organizations,
            organizations_change_percentage=orgs_change,
            total_tournaments=total_tournaments,
            tournaments_change_percentage=tournaments_change,
            total_teams=total_teams,
            teams_change_percentage=teams_change,
            users_last_6_months=users_last_6_months,
            last_6_months=last_6_months
        )
    
