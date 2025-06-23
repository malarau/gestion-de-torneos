"""
Decoradores para controlar el acceso basado en roles contextuales.
"""

from functools import wraps
from flask import abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import and_

def admin_required(f):
    """
    Decorador para rutas que requieren privilegios de administrador de plataforma.
    
    Uso:
    @app.route('/admin/activities')
    @login_required
    @admin_required
    def create_activity():
        return render_template('admin/create_activity.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"Checking admin access for user: {current_user.id}", flush=True)
        print(f"User is authenticated: {current_user.is_authenticated}", flush=True)
        print(f"User is admin: {current_user.is_admin}", flush=True)
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def organization_member_required(organization_param='organization_id'):
    """
    Decorador para verificar que el usuario sea miembro de la organización.
    
    Args:
        organization_param: Nombre del parámetro en la URL que contiene el organization_id
    
    Uso:
    @app.route('/organization/<int:organization_id>/events')
    @login_required
    @organization_member_required()
    def list_events(organization_id):
        return render_template('events/list.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flaskapp.database.models import OrganizationMember
            
            # Obtener organization_id de los argumentos de la ruta
            organization_id = kwargs.get(organization_param)
            if not organization_id:
                # Si no está en kwargs, intentar obtenerlo de view_args
                organization_id = request.view_args.get(organization_param)
            
            if not organization_id:
                abort(400)  # Bad Request si no se encuentra el parámetro
            
            # Verificar membresía
            membership = OrganizationMember.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not membership and not current_user.is_admin:
                flash('No tienes acceso a esta organización.', 'danger')
                return redirect(url_for('organizations_blueprint.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def organization_organizer_required(organization_param='organization_id'):
    """
    Decorador para verificar que el usuario sea organizador de la organización.
    
    Uso:
    @app.route('/organization/<int:organization_id>/tournaments/create')
    @login_required
    @organization_organizer_required()
    def create_tournament(organization_id):
        return render_template('tournaments/create.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flaskapp.database.models import OrganizationMember
            
            organization_id = kwargs.get(organization_param) or request.view_args.get(organization_param)
            if not organization_id:
                abort(400)
            
            # Verificar que sea organizador
            membership = OrganizationMember.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id,
                is_organizer=True
            ).first()
            
            if not membership:
                flash('No tienes permisos de organizador en esta organización.', 'danger')
                return redirect(url_for('organizations_blueprint.detail', organization_id=organization_id))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def tournament_referee_required(tournament_param='tournament_id'):
    """
    Decorador para verificar que el usuario sea árbitro del torneo.
    
    Uso:
    @app.route('/tournament/<int:tournament_id>/match/<int:match_id>/record')
    @login_required
    @tournament_referee_required()
    def record_match_result(tournament_id, match_id):
        return render_template('matches/record.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flaskapp.database.models import TournamentReferee
            
            tournament_id = kwargs.get(tournament_param) or request.view_args.get(tournament_param)
            if not tournament_id:
                abort(400)
            
            # Verificar que sea árbitro del torneo
            referee = TournamentReferee.query.filter_by(
                tournament_id=tournament_id,
                user_id=current_user.id
            ).first()
            
            if not referee:
                flash('No tienes permisos de árbitro en este torneo.', 'danger')
                return redirect(url_for('matches_blueprint.detail', organization_id=kwargs.get('organization_id'), tournament_id=tournament_id, match_id=kwargs.get('match_id')))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def team_leader_required(team_param='team_id'):
    """
    Decorador para verificar que el usuario sea líder del equipo.
    
    Uso:
    @app.route('/team/<int:team_id>/invite')
    @login_required
    @team_leader_required()
    def invite_team_member(team_id):
        return render_template('teams/invite.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flaskapp.database.models import TeamMember
            
            team_id = kwargs.get(team_param) or request.view_args.get(team_param)
            if not team_id:
                abort(400)
            
            # Verificar que sea líder del equipo
            membership = TeamMember.query.filter_by(
                team_id=team_id,
                user_id=current_user.id,
                is_leader=True
            ).first()
            
            if not membership:
                flash('No tienes permisos de líder en este equipo.', 'danger')
                return redirect(url_for('teams_blueprint.detail', organization_id=kwargs.get('organization_id'), tournament_id=kwargs.get('tournament_id'), team_id=team_id))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def team_member_required(team_param='team_id'):
    """
    Decorador para verificar que el usuario sea miembro del equipo.
    
    Uso:
    @app.route('/team/<int:team_id>/details')
    @login_required
    @team_member_required()
    def team_details(team_id):
        return render_template('teams/details.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flaskapp.database.models import TeamMember
            
            team_id = kwargs.get(team_param) or request.view_args.get(team_param)
            if not team_id:
                abort(400)
            
            # Verificar que sea miembro del equipo
            membership = TeamMember.query.filter_by(
                team_id=team_id,
                user_id=current_user.id
            ).first()
            
            if not membership:
                flash('No eres miembro de este equipo.', 'danger')
                return redirect(url_for('team_blueprint.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def tournament_participant_allowed(tournament_param='tournament_id'):
    """
    Decorador para verificar que el usuario puede participar en el torneo
    (no es árbitro y no está ya en otro equipo del mismo torneo).
    
    Uso:
    @app.route('/tournament/<int:tournament_id>/create-team')
    @login_required
    @organization_member_required('organization_id')  # Se debe combinar con otros
    @tournament_participant_allowed()
    def create_team(tournament_id):
        return render_template('teams/create.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flaskapp.database.models import TournamentReferee, TeamMember, Team
            from sqlalchemy import and_
            
            tournament_id = kwargs.get(tournament_param) or request.view_args.get(tournament_param)
            if not tournament_id:
                abort(400)
            
            # Verificar que no sea árbitro del torneo
            is_referee = TournamentReferee.query.filter_by(
                tournament_id=tournament_id,
                user_id=current_user.id
            ).first()
            
            if is_referee:
                flash('No puedes participar como jugador siendo árbitro del torneo.', 'danger')
                return redirect(url_for('tournament_blueprint.detail', tournament_id=tournament_id))
            
            # Verificar que no esté ya en otro equipo del torneo
            existing_team = TeamMember.query.join(Team).filter(
                and_(
                    Team.tournament_id == tournament_id,
                    TeamMember.user_id == current_user.id
                )
            ).first()
            
            if existing_team:
                flash('Ya estás participando en este torneo con otro equipo.', 'danger')
                return redirect(url_for('tournament_blueprint.detail', tournament_id=tournament_id))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def resource_owner_or_admin_required(resource_param='user_id'):
    """
    Decorador para verificar que el usuario sea propietario del recurso o admin.
    Útil para perfiles de usuario, configuraciones personales, etc.
    
    Uso:
    @app.route('/user/<int:user_id>/profile')
    @login_required
    @resource_owner_or_admin_required()
    def user_profile(user_id):
        return render_template('users/profile.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = kwargs.get(resource_param) or request.view_args.get(resource_param)
            if not user_id:
                abort(400)
            
            # Permitir si es el propio usuario o es admin
            if current_user.id != user_id and not current_user.is_admin:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Decorador combinado para casos comunes
def tournament_access_required(require_organizer=False, require_referee=False):
    """
    Decorador combinado para acceso a torneos con diferentes niveles de permisos.
    
    Args:
        require_organizer: Si True, requiere ser organizador de la organización
        require_referee: Si True, requiere ser árbitro del torneo
    
    Uso:
    @app.route('/tournament/<int:tournament_id>/manage')
    @login_required
    @tournament_access_required(require_organizer=True)
    def manage_tournament(tournament_id):
        return render_template('tournaments/manage.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flaskapp.database.models import Tournament, OrganizationMember, TournamentReferee
            
            tournament_id = kwargs.get('tournament_id') or request.view_args.get('tournament_id')
            if not tournament_id:
                abort(400)
            
            # Obtener el torneo para conocer la organización
            tournament = Tournament.query.get_or_404(tournament_id)
            
            # Verificar membresía básica en la organización
            membership = OrganizationMember.query.filter_by(
                organization_id=tournament.organization_id,
                user_id=current_user.id
            ).first()
            
            if not membership:
                flash('No tienes acceso a esta organización.', 'danger')
                return redirect(url_for('organizations_blueprint.index'))
            
            # Verificar permisos específicos
            if require_organizer and not membership.is_organizer:
                flash('Necesitas permisos de organizador.', 'danger')
                return redirect(url_for('tournament_blueprint.detail', tournament_id=tournament_id))
            
            if require_referee:
                referee = TournamentReferee.query.filter_by(
                    tournament_id=tournament_id,
                    user_id=current_user.id
                ).first()
                
                if not referee:
                    flash('Necesitas ser árbitro de este torneo.', 'error')
                    return redirect(url_for('tournament_blueprint.detail', tournament_id=tournament_id))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator