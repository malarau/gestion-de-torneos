from dataclasses import dataclass
from typing import List

@dataclass
class DashboardStatsDTO:
    total_users: int
    users_change_percentage: float
    total_organizations: int
    organizations_change_percentage: float
    total_tournaments: int
    tournaments_change_percentage: float
    total_teams: int
    teams_change_percentage: float
    users_last_6_months: List[int]
    last_6_months: List[str]