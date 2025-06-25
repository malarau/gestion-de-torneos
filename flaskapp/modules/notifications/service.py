from datetime import datetime
from typing import List
from flaskapp.database.models import Event, EventStatus, OrganizationMember, Tournament
from flaskapp.modules.notifications.dto import NotificationDTO

from flaskapp.database.models import db

class NotificationService:
    @staticmethod
    def get_notifications(c_id: int) -> List[dict]:
        from flaskapp.database.models import Notification
        notifications = Notification.query.filter_by(
            user_id=str(c_id)
            ).order_by(Notification.created_at.desc()).all()
        
        return [
            NotificationDTO(
                id= n.id,
                user_id = n.user_id,   
                title=n.title,
                message = n.message,
                is_read = n.is_read,
                type_id = n.type_id,
                related_entity_type_id = n.related_entity_type_id,
                related_entity_id = n.related_entity_id,
                created_at = n.created_at.strftime('%d-%m-%Y %H:%M:%S')
             ) for n in notifications
        ]
    
    @staticmethod
    def get_notification(c_id: int) -> List[dict]:
            from flaskapp.database.models import Notification
            notifications = Notification.query.filter_by(
                id=str(c_id)
                ).order_by(Notification.created_at.desc()).all()
            
            return [
                NotificationDTO(
                    id= n.id,
                    user_id = n.user_id,   
                    title=n.title,
                    message = n.message,
                    is_read = n.is_read,
                    type_id = n.type_id,
                    related_entity_type_id = n.related_entity_type_id,
                    related_entity_id = n.related_entity_id,
                    created_at = n.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ) for n in notifications
            ]
    
# Revizar 
    # @staticmethod
    # def mark_notification_as_read(notification_id: int, user_id: int):
    #     from flaskapp.database.models import Notification
    #     notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()
    #     notification.is_read = True
    #     db.session.commit()


"""
class EventService:
    @staticmethod
    def get_organization_events(organization_id: int, user_id: int) -> List[EventDTO]:
        from flaskapp.database.models import OrganizationMember
        is_organizer = OrganizationMember.query.filter_by(
            organization_id=organization_id,
            user_id=user_id,
            is_organizer=True
        ).first() is not None

        events = Event.query.filter_by(
            organization_id=organization_id
        ).options(
            db.joinedload(Event.organization),
            db.joinedload(Event.status)
        ).order_by(Event.start_date.desc()).all()

        return [
            EventDTO(
                id=e.id,
                name=e.name,
                description=e.description,
                start_date=e.start_date.strftime('%Y-%m-%d'),
                end_date=e.end_date.strftime('%Y-%m-%d'),
                status=e.status.code,
                organization_id=e.organization_id,
                organization_name=e.organization.name,
                can_edit=is_organizer
            ) for e in events
        ]

    @staticmethod
    def get_event_detail(event_id: int, user_id: int) -> EventDetailDTO:
        event = Event.query.options(
            db.joinedload(Event.organization),
            db.joinedload(Event.status),
            db.joinedload(Event.creator),
            db.joinedload(Event.tournaments).joinedload(Tournament.activity),
            db.joinedload(Event.tournaments).joinedload(Tournament.status)
        ).get_or_404(event_id)

        is_organizer = OrganizationMember.query.filter_by(
            organization_id=event.organization_id,
            user_id=user_id,
            is_organizer=True
        ).first() is not None

        status_options = EventStatus.query.order_by(EventStatus.id).all()

        # Ordenar los torneos por fecha de inicio
        sorted_tournaments = sorted(event.tournaments, key=lambda t: t.start_date or datetime.min)

        return EventDetailDTO(
            id=event.id,
            name=event.name,
            description=event.description,
            start_date=event.start_date.strftime('%Y-%m-%d'),
            end_date=event.end_date.strftime('%Y-%m-%d'),
            status=event.status.code,
            organization_id=event.organization_id,
            organization_name=event.organization.name,
            can_edit=is_organizer,
            creator_name=event.creator.name,
            created_at=event.created_at.strftime('%Y-%m-%d'),
            updated_at=event.updated_at.strftime('%Y-%m-%d') if event.updated_at else '',
            tournaments_count=len(event.tournaments),
            status_options=[{'code': s.code, 'description': s.description} for s in status_options],
            tournaments=[{
                'id': t.id,
                'name': t.name,
                'activity_name': t.activity.name if t.activity else 'N/A',
                'start_date': t.start_date.strftime('%Y-%m-%d') if t.start_date else 'N/A',
                'end_date': t.end_date.strftime('%Y-%m-%d') if t.end_date else 'N/A',
                'status': t.status.code
            } for t in sorted_tournaments]
        )

    @staticmethod
    def create_or_update_event(form_data, organization_id, creator_id, event_id=None):
            if event_id:
            event = Event.query.get_or_404(event_id)
        else:
            event = Event(
                organization_id=organization_id,
                created_by=creator_id
            )
            db.session.add(event)

        event.name = form_data['name']
        event.description = form_data['description']
        event.start_date = form_data['start_date']
        event.end_date = form_data['end_date']

        # Este bloque previene el autoflush prematuro
        with db.session.no_autoflush:
            status_code = form_data['status'].strip().upper()
            status = EventStatus.query.filter_by(code=status_code).first()
            if not status:
                raise ValueError(f"Estado '{status_code}' no encontrado en la base de datos.")
            event.status_id = status.id

        db.session.commit()
        return event
"""