from dataclasses import dataclass
from typing import List, Optional
from dataclasses import dataclass
from typing import List

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

@dataclass
class ActivityTournamentStats:
    id: int
    name: str
    organization_name: str
    organization_id: int
    status: str
    start_date: str

@dataclass
class ActivityStats:
    total_tournaments: int
    percentage_of_all: float
    total_teams: int
    total_participants: int
    recent_tournaments: List[ActivityTournamentStats]
    popular_organizations: List[dict]