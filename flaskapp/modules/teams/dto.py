from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class TeamMatchDTO:
    id: int
    level: int
    match_number: int
    team_a_id: int
    team_a_name: str
    team_a_score: Optional[int]
    team_a_leader: Optional[str]
    team_a_leader_pic: Optional[str]
    team_b_id: int
    team_b_name: str
    team_b_score: Optional[int]
    team_b_leader: Optional[str]
    team_b_leader_pic: Optional[str]
    winner_id: Optional[int]
    status: str
    completed_at: Optional[datetime]
    best_player_name: Optional[str]
    best_player_pic: Optional[str]

@dataclass
class TeamMemberDTO:
    user_id: int
    name: str
    email: str
    profile_picture: Optional[str]
    is_leader: bool
    joined_at: datetime

@dataclass
class TeamInvitationDTO:
    id: int
    invited_user_id: int
    invited_user_name: str
    invited_user_email: str
    invited_user_profile_picture: str
    status: str
    created_at: datetime

@dataclass
class EligibleMemberDTO:
    user_id: int
    name: str
    email: str
    profile_picture: Optional[str]
    is_invited: bool