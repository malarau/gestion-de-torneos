from dataclasses import dataclass
from typing import List, Optional

""" index() """
""" Página principal de organizaciones """
@dataclass
class OrganizationDTO:
    id: int
    name: str
    description: str
    member_count: int
    is_organizer: bool
    is_member: bool
    created_at: str

@dataclass
class OrganizationListDTO:
    organizations: List[OrganizationDTO]

@dataclass 
class OrganizationGroupsDTO:
    my_organizations: List[OrganizationDTO]  # Donde tengo relación
    other_organizations: List[OrganizationDTO]  # Disponibles para unirse

@dataclass
class PaginatedOrganizationsDTO:
    items: List[OrganizationDTO]
    page: int
    per_page: int
    total: int
    pages: int

""" detail()"""
""" Detalles de una organización específica"""

@dataclass
class OrganizationDetailDTO:
    id: int
    name: str
    description: str
    created_at: str
    creator_name: str
    member_count: int
    current_event: Optional['EventDTO']
    current_tournament: Optional['TournamentDTO']
    past_tournaments: List['TournamentDTO']
    is_organizer: bool

@dataclass
class EventDTO:
    id: int
    name: str
    description: str
    start_date: str
    end_date: str
    status: str

@dataclass
class TournamentDTO:
    id: int
    name: str
    activity_name: str
    start_date: str
    end_date: str
    status: str
    team_count: int

@dataclass
class MemberDTO:
    id: int
    user_id: int
    name: str
    email: str
    is_organizer: bool
    is_admin: bool