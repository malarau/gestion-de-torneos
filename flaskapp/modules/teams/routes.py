from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .forms import TeamForm
from .service import TeamService
from flaskapp.modules.auth.decorators import organization_member_required, team_leader_required
from flaskapp.database.models import Tournament

teams_bp = Blueprint(
    'teams_blueprint',
    __name__,
    url_prefix='/organizations/<int:organization_id>/tournaments/<int:tournament_id>/teams'
)

@teams_bp.route('/manage/', methods=['GET', 'POST'])
@login_required
@organization_member_required()
def create(organization_id, tournament_id):
    form = TeamForm()
    search_query = request.args.get('search', '')
    
    # Se pasa team_id=None porque aún no existe
    eligible_members = TeamService.get_eligible_members(tournament_id, None, search_query)

    if form.validate_on_submit():
        try:
            new_team = TeamService.create_team(
                organization_id=organization_id,
                tournament_id=tournament_id,
                name=form.name.data,
                leader_id=current_user.id
            )
            flash('Equipo creado correctamente', 'success')
            return redirect(url_for('teams_blueprint.manage',
                                    organization_id=organization_id,
                                    tournament_id=tournament_id,
                                    team_id=new_team.id))
        except Exception as e:
            flash(str(e), 'danger')

    return render_template(
        'teams/manage.html',
        segment='Equipos',
        team=None,
        form=form,
        eligible_members=eligible_members,
        search_query=search_query,
        organization_id=organization_id,
        tournament_id=tournament_id,
        team_id=None
    )

@teams_bp.route('/manage/<int:team_id>', methods=['GET', 'POST'])
@login_required
@organization_member_required()
@team_leader_required()
def manage(organization_id, tournament_id, team_id):
    team = TeamService.get_team_details(team_id)
    form = TeamForm(obj=team)
    search_query = request.args.get('search', '')

    eligible_members = TeamService.get_eligible_members(tournament_id, team_id, search_query)

    if form.validate_on_submit():
        try:
            TeamService.update_team(team_id, form.name.data)
            flash('Equipo actualizado correctamente', 'success')
            return redirect(url_for('teams_blueprint.manage',
                                    organization_id=organization_id,
                                    tournament_id=tournament_id,
                                    team_id=team_id))
        except Exception as e:
            flash(str(e), 'danger')

    return render_template(
        'teams/manage.html',
        segment='Equipos',
        team=team,
        form=form,
        eligible_members=eligible_members,
        search_query=search_query,
        organization_id=organization_id,
        tournament_id=tournament_id,
        team_id=team_id
    )


@teams_bp.route('/<int:team_id>')
@login_required
@organization_member_required()
def detail(organization_id, tournament_id, team_id):
    team = TeamService.get_team_details(team_id)
    members = TeamService.get_team_members(team_id)
    invitations = TeamService.get_team_invitations(team_id)
    matches = TeamService.get_team_matches(team_id)
    is_leader = TeamService.is_team_leader(team_id, current_user.id)
    
    tournament = Tournament.query.get_or_404(tournament_id)
    
    return render_template(
        'teams/detail.html',
        segment='Equipos',
        team=team,
        members=members,
        invitations=invitations,
        matches=matches,
        tournament=tournament,
        organization_id=organization_id,
        tournament_id=tournament_id,
        is_leader=is_leader
    )

@teams_bp.route('/toggle-invite/<int:team_id>/<int:user_id>')
@login_required
@team_leader_required()
def toggle_invite(organization_id, tournament_id, team_id, user_id):
    try:
        result = TeamService.toggle_invitation(tournament_id, team_id, user_id)
        if result == 'added':
            flash('Invitación enviada', 'success')
        else:
            flash('Invitación cancelada', 'info')
    except Exception as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('teams_blueprint.manage', 
                          organization_id=organization_id, 
                          tournament_id=tournament_id, 
                          team_id=team_id,
                          search=request.args.get('search', '')))

@teams_bp.route('/delete/<int:team_id>')
@login_required
@team_leader_required()
def delete_team(organization_id, tournament_id, team_id):
    try:
        TeamService.delete_team(team_id)
        flash('Equipo eliminado correctamente', 'success')
        return redirect(url_for('tournaments_blueprint.detail', 
                              organization_id=organization_id, 
                              tournament_id=tournament_id))
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('teams_blueprint.manage', 
                              organization_id=organization_id, 
                              tournament_id=tournament_id, 
                              team_id=team_id))