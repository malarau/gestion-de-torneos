from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from flaskapp.modules.profile.forms import ProfileForm
from flaskapp.modules.profile.service import ProfileService

from flaskapp.database.models import db

profile_blueprint = Blueprint(
    'profile_blueprint',
    __name__,
    url_prefix='/profile'
)

@profile_blueprint.route('/<int:user_id>', methods=['GET', 'POST'])
@profile_blueprint.route('/', methods=['GET', 'POST'], defaults={'user_id': None})
@login_required
def profile(user_id):
    # Si no se especifica ID, mostrar perfil del usuario actual
    profile_user_id = user_id if user_id else current_user.id
    form = ProfileForm()
    
    if form.validate_on_submit() and profile_user_id == current_user.id:
        try:
            ProfileService.update_profile(profile_user_id, form.data)
            flash('Perfil actualizado correctamente', 'success')
            return redirect(url_for('profile_blueprint.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    profile_data = ProfileService.get_user_profile(profile_user_id, current_user.id)
    
    # Añadir estadísticas
    if profile_user_id:
        profile_data.stats = ProfileService.get_user_stats(profile_user_id)
    
    if profile_user_id == current_user.id:
        form.name.data = profile_data.name
        form.email.data = profile_data.email

    return render_template(
        'profile/profile.html',
        profile=profile_data,
        form=form if profile_data.is_current_user else None,
        segment='profile'
    )