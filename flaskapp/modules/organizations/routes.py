from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from flaskapp.database.models import Organization
from flaskapp.modules.auth.decorators import (
    admin_required, 
    organization_member_required
)
from flaskapp.modules.organizations.forms import OrganizationForm
from flaskapp.modules.organizations.service import OrganizationService

from flaskapp.database.models import db

org_bp = Blueprint(
    'organizations_blueprint',
    __name__,
    url_prefix='/organizations'
)

@org_bp.route('/')
@login_required
def index():
    """Página principal de organizaciones"""
    my_orgs, other_orgs = OrganizationService.get_organization_groups()

    print(f"\n{my_orgs=}", flush=True)
    # print is admin
    print(f"{current_user.is_admin=}", flush=True)
    return render_template(
        'organizations/index.html',
        my_orgs=my_orgs,
        other_orgs=other_orgs,
        segment='Organizaciones'
    )

@org_bp.route('/manage/', methods=['GET', 'POST'])
@org_bp.route('/manage/<int:organization_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_organization(organization_id=None):
    # Manejar creación/edición de organización
    form = OrganizationForm()
    org = None
    
    if organization_id:
        org = Organization.query.get_or_404(organization_id)
        form = OrganizationForm(obj=org)

    # Manejar búsqueda y gestión de organizadores (solo en edición)
    members = []
    search_query = ''
    if organization_id:
        search_query = request.args.get('search', '')
        members = OrganizationService.get_organization_members(organization_id, search_query)
        
        # Manejar cambio de rol de organizador
        if 'toggle_organizer' in request.args:
            try:
                OrganizationService.toggle_organizer(
                    int(request.args['toggle_organizer']),
                    organization_id
                )
                flash('Rol de organizador actualizado', 'success')
                return redirect(url_for('organizations_blueprint.manage_organization', 
                                    organization_id=organization_id,
                                    search=search_query))
            except ValueError as e:
                flash(str(e), 'danger')
                db.session.rollback()

    # Manejar envío del formulario principal
    if form.validate_on_submit():
        try:
            OrganizationService.create_or_update_organization(
                form.data,
                organization_id=organization_id,
                creator_id=current_user.id
            )
            flash('Organización guardada exitosamente', 'success')
            return redirect(url_for('organizations_blueprint.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')

    return render_template(
        'organizations/manage.html',
        form=form,
        organization=org,
        is_edit=organization_id is not None,
        members=members,
        search_query=search_query,
        segment='Organizaciones'
    )

@org_bp.route('/<int:organization_id>')
@login_required
@organization_member_required()
def detail(organization_id):
    """Solo miembros pueden ver detalles de la organización"""
    org_details = OrganizationService.get_organization_details(organization_id, current_user.id)
    return render_template(
        'organizations/detail.html',
        org=org_details,
        segment='Organizaciones'
    )


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

