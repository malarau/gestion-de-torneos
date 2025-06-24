from collections import defaultdict
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from flaskapp.database.models import Tournament, db
from flaskapp.modules.auth.decorators import organization_member_required, organization_organizer_required
from flaskapp.modules.tournaments.forms import TournamentForm
from flaskapp.modules.tournaments.service import TournamentService

tournaments_bp = Blueprint(
    'tournaments_blueprint',
    __name__,
    url_prefix='/organizations/<int:organization_id>/tournaments/'
)

@tournaments_bp.route('/')
@login_required
@organization_member_required()
def index(organization_id):
    tournaments = TournamentService.get_organization_tournaments(organization_id, current_user.id)
    return render_template(
        'tournaments/index.html',
        tournaments=tournaments,
        organization_id=organization_id,
        segment='Torneos'
    )

@tournaments_bp.route('/<int:tournament_id>/cancel', methods=['GET'])
@login_required
@organization_member_required()
def cancel_tournament(organization_id, tournament_id):
    tournament = TournamentService.get_tournament_detail(tournament_id, current_user.id)
    
    if not tournament:
        flash('Torneo no encontrado', 'danger')
        return redirect(url_for('tournaments_blueprint.index', organization_id=organization_id))
    
    try:
        TournamentService.cancel_tournament(tournament_id)
        flash('Torneo cancelado exitosamente', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        current_app.logger.error(f"Error canceling tournament: {str(e)}")
        flash('Ocurrió un error al cancelar el torneo', 'danger')
    
    return redirect(url_for('tournaments_blueprint.detail', organization_id=organization_id, tournament_id=tournament_id))

@tournaments_bp.route('/<int:tournament_id>/start', methods=['GET'])
@login_required
@organization_member_required()
def start_tournament(organization_id, tournament_id):
    tournament = TournamentService.get_tournament_detail(tournament_id, current_user.id)
    
    if not tournament:
        flash('Torneo no encontrado', 'danger')
        return redirect(url_for('tournaments_blueprint.index', organization_id=organization_id))
    
    try:
        TournamentService.start_tournament(tournament_id)
        flash('Torneo iniciado exitosamente', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        current_app.logger.error(f"Error starting tournament: {str(e)}")
        flash('Ocurrió un error al iniciar el torneo', 'danger')
    
    return redirect(url_for('tournaments_blueprint.detail', organization_id=organization_id, tournament_id=tournament_id))

@tournaments_bp.route('/<int:tournament_id>')
@login_required
@organization_member_required()
def detail(organization_id, tournament_id):
    tournament = TournamentService.get_tournament_detail(tournament_id, current_user.id)
    can_create_team = TournamentService.can_create_team(tournament_id, current_user.id)
    pending_invitations = TournamentService.get_user_pending_invitations(tournament_id, current_user.id)
    
    matches = TournamentService.get_tournament_matches(tournament_id)
    bracket_by_level = defaultdict(list)
    for match in matches:
        bracket_by_level[match.level].append(match)
    bracket_by_level = dict(sorted(bracket_by_level.items(), reverse=True))

    return render_template(
        'tournaments/detail.html',
        tournament=tournament,
        organization_id=organization_id,
        can_create_team=can_create_team,
        tournament_id=tournament_id,
        pending_invitations=pending_invitations,
        bracket_by_level=bracket_by_level,
        segment='Torneos'
    )

@tournaments_bp.route('/manage', methods=['GET', 'POST'])
@tournaments_bp.route('/manage/<int:tournament_id>', methods=['GET', 'POST'])
@login_required
@organization_organizer_required()
def manage(organization_id, tournament_id=None):
    form = TournamentForm(organization_id=organization_id)
    tournament = None
    referees = []
    search_query = ''
    
    if tournament_id:
        tournament = Tournament.query.get_or_404(tournament_id)
        form = TournamentForm(organization_id=organization_id, obj=tournament)
        search_query = request.args.get('search', '')
        referees = TournamentService.get_eligible_referees(tournament_id, search_query)
        
        if 'toggle_referee' in request.args:
            try:
                action = TournamentService.toggle_referee(
                    tournament_id,
                    int(request.args['toggle_referee'])
                )
                flash(f'Árbitro {"agregado" if action == "added" else "eliminado"}', 'success')
                return redirect(url_for('tournaments_blueprint.manage', 
                                    organization_id=organization_id,
                                    tournament_id=tournament_id,
                                    search=search_query))
            except ValueError as e:
                flash(str(e), 'danger')
                db.session.rollback()

    if form.validate_on_submit():
        try:
            tournament = TournamentService.create_or_update_tournament(
                form, organization_id, tournament_id
            )
            flash('Torneo guardado exitosamente', 'success')
            return redirect(url_for('tournaments_blueprint.manage', 
                                organization_id=organization_id,
                                tournament_id=tournament.id))
        except ValueError as e:
            flash(str(e), 'danger')
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving tournament: {str(e)}")
            flash('Ocurrió un error al guardar el torneo', 'danger')

    return render_template(
        'tournaments/manage.html',
        form=form,
        tournament=tournament,
        referees=referees,
        search_query=search_query,
        organization_id=organization_id,
        segment='Torneos'
    )


@tournaments_bp.route('/<int:tournament_id>/invitations/<int:invitation_id>/accept', methods=['POST'])
@login_required
@organization_member_required()
def accept_invitation(organization_id, tournament_id, invitation_id):
    try:
        TournamentService.accept_invitation(invitation_id, current_user.id)
        flash('¡Invitación aceptada con éxito! Ahora eres parte del equipo.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('Ocurrió un error al procesar tu solicitud', 'danger')
    
    return redirect(url_for('tournaments_blueprint.detail', organization_id=organization_id, tournament_id=tournament_id))


@tournaments_bp.route('/<int:tournament_id>/invitations/<int:invitation_id>/reject', methods=['POST'])
@login_required
@organization_member_required()
def reject_invitation(organization_id, tournament_id, invitation_id):
    try:
        TournamentService.reject_invitation(invitation_id, current_user.id)
        flash('Invitación rechazada', 'info')
    except Exception:
        flash('Ocurrió un error al procesar tu solicitud', 'danger')
    
    return redirect(url_for('tournaments_blueprint.detail', organization_id=organization_id, tournament_id=tournament_id))


