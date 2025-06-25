from dataclasses import dataclass
from typing import List


@dataclass
class UserProfileDTO:
    id: int
    name: str
    email: str
    profile_picture: str
    created_at: str
    is_current_user: bool
    common_organizations: List[dict]  # {id: int, name: str, is_organizer: bool}

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TournamentStats:
    id: int
    name: str
    organization_name: str
    organization_id: int
    status: str
    status_display: str

@dataclass
class UserStats:
    tournaments_played: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    win_rate: float = 0.0
    favorite_activity: Optional[str] = None
    favorite_activity_count: int = 0
    referee_count: int = 0
    leader_count: int = 0
    recent_tournaments: List[TournamentStats] = None