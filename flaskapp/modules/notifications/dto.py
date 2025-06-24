from dataclasses import dataclass
from typing import List, Optional
from datetime import date

@dataclass
class EventDTO:
    id: int
    name: str
    description: str
    start_date: str
    end_date: str
    status: str
    organization_id: int
    organization_name: str
    can_edit: bool

@dataclass
class EventDetailDTO(EventDTO):
    creator_name: str
    created_at: str
    updated_at: str
    tournaments_count: int
    status_options: List[dict]