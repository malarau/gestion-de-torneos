from flask import abort
from flaskapp.database.models import Organization, User
from flaskapp.modules.profile.dto import UserProfileDTO

from flaskapp.database.models import OrganizationMember, db

class ProfileService:
    @staticmethod
    def get_user_profile(user_id: int, current_user_id: int) -> UserProfileDTO:
        user = User.query.get_or_404(user_id)
        
        common_orgs = []
        if user_id != current_user_id:
            # Obtener organizaciones en común
            common_orgs = db.session.query(
                Organization.id,
                Organization.name,
                OrganizationMember.is_organizer
            ).join(
                OrganizationMember,
                Organization.id == OrganizationMember.organization_id
            ).filter(
                OrganizationMember.user_id == current_user_id,
                Organization.id.in_(
                    db.session.query(OrganizationMember.organization_id)
                    .filter(OrganizationMember.user_id == user_id)
                )
            ).all()
            
            if not common_orgs:
                abort(403)

        return UserProfileDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_picture=user.profile_picture or '/static/assets/img/theme/default-profile.png',
            created_at=user.created_at.strftime('%d. %B %Y'),
            is_current_user=(user_id == current_user_id),
            common_organizations=[{
                'id': org.id,
                'name': org.name,
                'is_organizer': org.is_organizer
            } for org in common_orgs]
        )

    @staticmethod
    def update_profile(user_id: int, form_data: dict):
        user = User.query.get_or_404(user_id)
        user.name = form_data['name']
        db.session.commit()
        return user
