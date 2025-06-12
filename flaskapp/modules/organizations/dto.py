from dataclasses import dataclass
from typing import List

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