from flask_login import current_user
from sqlalchemy import func
from flaskapp.database.models import User, db, Organization, OrganizationMember
from .dto import OrganizationDTO, OrganizationGroupsDTO, OrganizationListDTO

def convert_to_dto(org: Organization, is_member: bool = False, is_organizer: bool = False) -> OrganizationDTO:
    return OrganizationDTO(
        id=org.id,
        name=org.name,
        description=org.description[:100] + '...' if org.description and len(org.description) > 100 else org.description or '',
        member_count=len(org.members),  # Asume relación backref 'members'
        is_organizer=is_organizer,
        is_member=is_member,
        created_at=org.created_at.strftime('%Y-%m-%d')
    )

class OrganizationService:
    @staticmethod
    def get_organization_groups() -> OrganizationGroupsDTO:
        # Obtener IDs de organizaciones donde el usuario ya es miembro/organizador
        user_orgs = db.session.query(
            OrganizationMember.organization_id,
            OrganizationMember.is_organizer
        ).filter(
            OrganizationMember.user_id == current_user.id
        ).all()

        org_ids = [org_id for org_id, _ in user_orgs]
        organizer_ids = [org_id for org_id, is_org in user_orgs if is_org]

        # Consulta optimizada para todas las organizaciones
        all_orgs = Organization.query.options(
            db.joinedload(Organization.members)
        ).order_by(Organization.name).all()

        # Clasificación
        my_orgs = []
        other_orgs = []
        
        for org in all_orgs:
            if org.id in org_ids:
                my_orgs.append(convert_to_dto(
                    org,
                    is_member=True,
                    is_organizer=(org.id in organizer_ids)
                ))
            else:
                other_orgs.append(convert_to_dto(org))

        return OrganizationGroupsDTO(
            my_organizations=sorted(my_orgs, key=lambda x: not x.is_organizer),
            other_organizations=other_orgs
        )
    
    @staticmethod
    def join_organization(user_id: int, org_id: int) -> tuple[bool, str]:
        """
        Intenta unir al usuario a una organización
        Retorna: (success: bool, message: str)
        """
        from flaskapp.database.models import db, Organization, OrganizationMember
        
        # Verificar si el usuario ya es miembro
        existing_membership = OrganizationMember.query.filter_by(
            user_id=user_id,
            organization_id=org_id
        ).first()
        
        if existing_membership:
            return False, "Ya eres miembro de esta organización"
        
        # Verificar si la organización existe
        organization = Organization.query.get(org_id)
        if not organization:
            return False, "Organización no encontrada"
        
        # Verificar si es admin de plataforma (no necesita unirse)
        user = User.query.get(user_id)
        if user.is_admin:
            return False, "Los administradores no necesitan unirse a organizaciones"
        
        try:
            # Crear nueva membresía
            new_member = OrganizationMember(
                organization_id=org_id,
                user_id=user_id,
                is_organizer=False  # Por defecto no es organizador
            )
            
            db.session.add(new_member)
            db.session.commit()
            
            return True, f"Te has unido exitosamente a {organization.name}"
        
        except Exception as e:
            db.session.rollback()
            return False, f"Error al unirse a la organización: {str(e)}"