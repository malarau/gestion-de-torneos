from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from flaskapp.modules.auth.decorators import (
    admin_required, 
    organization_member_required, 
    organization_organizer_required
)
from flaskapp.modules.organizations.service import OrganizationService

org_bp = Blueprint(
    'organizations_blueprint',
    __name__,
    url_prefix='/organizations'
)

@org_bp.route('/')
@login_required
def index():
    """Página principal de organizaciones"""
    org_data = OrganizationService.get_organization_groups()
    print("\n\n\n*****Organization groups data:\n", org_data, flush=True)
    
    return render_template('organizations/index.html', org_data=org_data)

@org_bp.route('/create')
@login_required
@admin_required
def create_organization():
    """Solo admins pueden crear organizaciones"""
    return render_template('organizations/create.html')

@org_bp.route('/<int:organization_id>/settings')
@login_required
@organization_organizer_required()
def settings(organization_id):
    """Solo organizadores pueden acceder a configuración"""
    return render_template('organization/settings.html')

@org_bp.route('/<int:organization_id>')
@login_required
@organization_member_required()
def detail(organization_id):
    """Solo miembros pueden ver detalles de la organización"""
    return render_template('organizations/detail.html')


@org_bp.route('/join/<int:organization_id>', methods=['POST'])
@login_required
def join(organization_id):
    print(f"Intentando unir al usuario {current_user.id} a la organización {organization_id}", flush=True)
    # Validar y unirse a la organización
    success, message = OrganizationService.join_organization(current_user.id, organization_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('organizations_blueprint.index'))

