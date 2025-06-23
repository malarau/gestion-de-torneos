from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MatchDTO:
    id: int
    tournament_id: int
    level: int
    match_number: int
    team_a_id: Optional[int]
    team_b_id: Optional[int]
    team_a_members: Optional[list]
    team_b_members: Optional[list]
    team_a_name: Optional[str]
    team_b_name: Optional[str]
    team_a_score: Optional[int]
    team_b_score: Optional[int]
    winner_id: Optional[int]
    best_player_id: Optional[int]
    best_player_name: Optional[str]
    best_player_pic: Optional[str]
    is_bye: bool
    status: str
    status_description: str
    completed_at: Optional[datetime]
    recorded_by_referee_id: Optional[int]
    recorded_by_referee_name: Optional[str]
    team_a_leader: Optional[dict]
    team_b_leader: Optional[dict]

@dataclass
class MatchUpdateDTO:
    score_team_a: Optional[int]
    score_team_b: Optional[int]
    best_player_id: Optional[int]
    status: str
    recorded_by_referee_id: int