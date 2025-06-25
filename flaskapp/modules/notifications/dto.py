# modules/notifications/dto.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class NotificationDTO:
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    type_id: int
    type_id: int
    related_entity_type_id: int
    related_entity_id: int
    created_at: datetime
