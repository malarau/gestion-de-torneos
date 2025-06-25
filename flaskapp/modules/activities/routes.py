

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flaskapp.database.models import Activity, db
from flaskapp.modules.activities.forms import ActivityForm
from flaskapp.modules.activities.service import ActivityService
from flaskapp.modules.auth.decorators import admin_required

activities_blueprint = Blueprint(
    'activities_blueprint',
    __name__,
    url_prefix='/activities'
)

@activities_blueprint.route('/')
@login_required
def index():
    activities = ActivityService.get_all_activities()
    return render_template(
        'activities/index.html',
        activities=activities,
        segment='Actividades'
    )

@activities_blueprint.route('/<int:activity_id>')
@login_required
def detail(activity_id):
    activity_data = ActivityService.get_complete_activity_details(
        activity_id,
        current_user.is_admin
    )
    
    return render_template(
        'activities/detail.html',
        activity=activity_data['activity'],
        stats=activity_data['stats']
    )

@activities_blueprint.route('/manage/', methods=['GET', 'POST'])
@activities_blueprint.route('/manage/<int:activity_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage(activity_id=None):
    form = ActivityForm()
    activity = None

    if activity_id:
        activity = Activity.query.get_or_404(activity_id)
        form = ActivityForm(obj=activity)

    if form.validate_on_submit():
        try:
            ActivityService.create_or_update_activity(
                form.data,
                activity_id
            )
            flash('Actividad guardada exitosamente', 'success')
            return redirect(url_for('activities_blueprint.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')

    return render_template(
        'activities/manage.html',
        form=form,
        activity=activity,
        is_edit=activity_id is not None,
        segment='Actividades'
    )

@activities_blueprint.route('/toggle/<int:activity_id>', methods=['POST'])
@login_required
@admin_required
def toggle(activity_id):
    activity = ActivityService.toggle_activity(activity_id)
    flash(f'Actividad {"activada" if activity.is_active else "desactivada"}', 'success')
    return redirect(request.referrer or url_for('activities_blueprint.index'))