from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ActivityDTO:
    id: int
    name: str
    description: str
    min_players: int
    category: Optional[str]
    is_active: bool
    created_by: str
    created_at: str
    updated_at: str

@dataclass
class ActivityDetailDTO(ActivityDTO):
    tournaments_count: int
    can_edit: bool