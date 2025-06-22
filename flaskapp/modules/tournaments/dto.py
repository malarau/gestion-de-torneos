from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class RefereeDTO:
    user_id: int  # Nuevo campo
    id: int
    name: str
    email: str
    profile_picture: str

@dataclass
class TournamentDTO:
    id: int
    name: str
    activity_name: str
    start_date: str
    end_date: str
    status: str
    max_teams: int
    team_count: int
    can_edit: bool
    is_team_creation_open: bool

@dataclass
class TeamMemberDTO:
    user_id: int
    name: str
    email: str
    profile_picture: str
    is_leader: bool

@dataclass
class TeamDTO:
    id: int
    name: str
    seed_score: int
    members: List[TeamMemberDTO]

@dataclass
class TournamentDetailDTO(TournamentDTO):
    description: str
    prizes: str
    created_by: str
    created_at: str
    updated_at: str
    referees: List[Dict[str, Any]]  # Tipo más específico
    organization_name: str
    event_name: Optional[str]
    activity_id: int  # Útil para formularios
    status_id: int  # Útil para formularios
    event_id: Optional[int]  # Útil para formularios
    teams: List[TeamDTO]
    user_has_team: bool

@dataclass
class EligibleRefereeDTO:
    id: int
    user_id: int
    name: str
    email: str
    is_referee: bool
    profile_picture: Optional[str]  # Útil para la UI

@dataclass
class TournamentFormDTO:
    """DTO específico para el formulario de torneo"""
    name: str
    description: Optional[str]
    activity_id: int
    max_teams: int
    start_date: datetime
    end_date: datetime
    prizes: Optional[str]
    status_id: int
    event_id: Optional[int]
    organization_id: int  # Para contexto de permisos