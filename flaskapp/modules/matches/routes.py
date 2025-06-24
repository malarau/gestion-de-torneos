from flask import Blueprint, render_template, abort, request
from flask_login import login_required, current_user
from flaskapp.database.models import Match, Organization, Tournament
from flaskapp.modules.auth.decorators import organization_member_required
from flaskapp.modules.matches.forms import MatchResultForm
from flaskapp.modules.matches.service import MatchService

matches_bp = Blueprint(
    'matches_blueprint',
    __name__,
    url_prefix='/organizations/<int:organization_id>/tournaments/<int:tournament_id>/matches'
)

@matches_bp.route('/<int:match_id>', methods=['GET'])
@login_required
@organization_member_required()
def detail(organization_id, tournament_id, match_id):
    # Obtener detalles del partido
    match = MatchService.get_match_details(match_id)
    if not match or match.tournament_id != tournament_id:
        abort(404)
    
    # Verificar si el usuario es árbitro del torneo
    is_referee = MatchService.is_user_tournament_referee(current_user.id, tournament_id)
    
    return render_template(
        'matches/detail.html',
        segment='Partidos',
        match=match,
        is_referee=is_referee,
        organization_id=organization_id,
        tournament_id=tournament_id
    )

@matches_bp.route('/manage/<int:match_id>', methods=['GET', 'POST'])
@login_required
@organization_member_required()
def manage(organization_id, tournament_id, match_id):
    from flask import redirect, flash, url_for

    match = Match.query.get_or_404(match_id)
    tournament = Tournament.query.get_or_404(tournament_id)

    # Verificar si el usuario es árbitro del torneo
    if not MatchService.is_user_tournament_referee(current_user.id, tournament_id):
        flash('No tienes permisos para gestionar este partido', 'danger')
        return redirect(url_for('matches_blueprint.detail', 
                             organization_id=organization_id,
                             tournament_id=tournament_id,
                             match_id=match_id))

    # Verificar condiciones para edición
    can_edit = MatchService.can_edit_match(match_id, current_user.id)
    if request.method == 'POST' and not can_edit:
        flash('No es posible editar este partido en este momento', 'danger')
        return redirect(url_for('matches_blueprint.detail', 
                             organization_id=organization_id,
                             tournament_id=tournament_id,
                             match_id=match_id))

    form = MatchResultForm()
    eligible_players = MatchService.get_eligible_players(match_id)
    form.best_player_id.choices = [(0, "Seleccionar jugador")] + [
        (p['id'], f"{p['name']} ({p['team']})") for p in eligible_players
    ]

    if form.validate_on_submit() and can_edit:
        update_data = {
            'score_team_a': form.score_team_a.data,
            'score_team_b': form.score_team_b.data,
            'best_player_id': form.best_player_id.data if form.best_player_id.data != 0 else None,
            'recorded_by_referee_id': current_user.id
        }

        if MatchService.update_match(match_id, update_data):
            flash('Resultados actualizados correctamente', 'success')
        else:
            flash('Error al actualizar los resultados', 'danger')

        return redirect(url_for('matches_blueprint.detail', 
                             organization_id=organization_id,
                             tournament_id=tournament_id,
                             match_id=match_id))

    elif request.method == 'GET':
        match_details = MatchService.get_match_details(match_id)
        form.score_team_a.data = match_details.team_a_score
        form.score_team_b.data = match_details.team_b_score
        form.best_player_id.data = match_details.best_player_id or 0

    return render_template(
        'matches/manage.html',
        segment='matches',
        form=form,
        match=MatchService.get_match_details(match_id),
        organization=Organization.query.get(organization_id),
        tournament=tournament,
        organization_id=organization_id,
        tournament_id=tournament_id,
        can_edit=can_edit,
        is_referee=True  # Porque pasó la verificación de árbitro
    )