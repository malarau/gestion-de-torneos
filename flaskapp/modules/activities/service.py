from typing import List
from flaskapp.database.models import Activity
from flaskapp.modules.activities.dto import ActivityDTO, ActivityDetailDTO

from flaskapp.database.models import db

class ActivityService:
    @staticmethod
    def get_all_activities() -> List[ActivityDTO]:
        activities = Activity.query.options(
            db.joinedload(Activity.creator),
            db.joinedload(Activity.category)
        ).all()
        return [
            ActivityDTO(
                id=a.id,
                name=a.name,
                description=a.description,
                min_players=a.min_players_per_team,
                category=a.category.name if a.category else None,
                is_active=a.is_active,
                created_by=a.creator.name if a.creator else 'Sistema',
                created_at=a.created_at.strftime('%Y-%m-%d'),
                updated_at=a.updated_at.strftime('%Y-%m-%d') if a.updated_at else ''
            ) for a in activities
        ]

    @staticmethod
    def get_activity_detail(activity_id: int, is_admin: bool) -> ActivityDetailDTO:
        activity = Activity.query.options(
            db.joinedload(Activity.creator),
            db.joinedload(Activity.category),
            db.joinedload(Activity.tournaments)
        ).get_or_404(activity_id)

        return ActivityDetailDTO(
            id=activity.id,
            name=activity.name,
            description=activity.description,
            min_players=activity.min_players_per_team,
            category=activity.category.name if activity.category else None,
            is_active=activity.is_active,
            created_by=activity.creator.name if activity.creator else 'Sistema',
            created_at=activity.created_at.strftime('%Y-%m-%d'),
            updated_at=activity.updated_at.strftime('%Y-%m-%d') if activity.updated_at else '',
            tournaments_count=len(activity.tournaments),
            can_edit=is_admin
        )

    @staticmethod
    def toggle_activity(activity_id: int):
        activity = Activity.query.get_or_404(activity_id)
        activity.is_active = not activity.is_active
        db.session.commit()
        return activity

    @staticmethod
    def create_or_update_activity(form_data, activity_id=None):
        if activity_id:
            activity = Activity.query.get_or_404(activity_id)
        else:
            activity = Activity()
            db.session.add(activity)

        activity.name = form_data['name']
        activity.description = form_data['description']
        activity.min_players_per_team = form_data['min_players']
        activity.category_id = form_data['category']
        activity.is_active = form_data['is_active']
        
        db.session.commit()
        return activity