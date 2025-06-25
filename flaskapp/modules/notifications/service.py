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
        print(f"Notifications for user {c_id}: {notifications}", flush=True)
        # Detalle completo de las notificaciones (id , user_id, title, message, is_read, type_id, related_entity_type_id, related_entity_id, created_at)
        for n in notifications:
            print(f"Notification ID: {n.id}, User ID: {n.user_id}, Title: {n.title}, Message: {n.message}, Is Read: {n.is_read}, Type ID: {n.type_id}, Related Entity Type ID: {n.related_entity_type_id}, Related Entity ID: {n.related_entity_id}, Created At: {n.created_at}", flush=True)
        
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
    
   