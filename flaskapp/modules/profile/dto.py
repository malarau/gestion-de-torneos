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