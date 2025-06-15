from flask import Blueprint, render_template
from flaskapp.database.models import Event, db

""" Using events_bp blueprint to avoid circular imports """
from flaskapp.modules.events.forms import EventForm
from flaskapp.modules.events.service import EventService

events_bp = Blueprint(
    'events_blueprint',
    __name__,
    url_prefix='/organizations/<int:organization_id>/events/'
)

from flask import request, redirect, url_for, flash
from flask_login import current_user, login_required
from flaskapp.modules.auth.decorators import (
    organization_member_required,
    organization_organizer_required
)

@events_bp.route('/')
@login_required
@organization_member_required()
def index(organization_id):
    events = EventService.get_organization_events(organization_id, current_user.id)
    return render_template(
        'events/index.html',
        events=events,
        organization_id=organization_id,
        segment='Eventos'
    )

@events_bp.route('/<int:event_id>')
@login_required
@organization_member_required()
def detail(organization_id, event_id):
    event = EventService.get_event_detail(event_id, current_user.id)
    return render_template(
        'events/detail.html',
        event=event,
        segment='Eventos'
    )

@events_bp.route('/manage', methods=['GET', 'POST'])
@events_bp.route('/manage/<int:event_id>', methods=['GET', 'POST'])
@login_required
@organization_organizer_required()
def manage(organization_id, event_id=None):
    form = EventForm()
    event = None

    if event_id:
        event = Event.query.get_or_404(event_id)
        form = EventForm(obj=event)
        form.status.data = event.status.code

    if form.validate_on_submit():
        try:
            EventService.create_or_update_event(
                form.data,
                organization_id,
                current_user.id,
                event_id
            )
            flash('Evento guardado exitosamente', 'success')
            return redirect(url_for('events_blueprint.index', organization_id=organization_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')

    return render_template(
        'events/manage.html',
        form=form,
        event=event,
        is_edit=event_id is not None,
        organization_id=organization_id,
        segment='Eventos'
    )