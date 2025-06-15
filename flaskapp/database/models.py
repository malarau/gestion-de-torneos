"""
Tournament System Database Models
SQLAlchemy models for the tournament management system.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ##############################
# SECCIÓN 1: Tablas de Estados y Tipos (Enums)
# ##############################

class EventStatus(db.Model):
    __tablename__ = 'event_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    events = db.relationship('Event', backref='status', lazy=True)

class TournamentStatus(db.Model):
    __tablename__ = 'tournament_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    tournaments = db.relationship('Tournament', backref='status', lazy=True)

class MatchStatus(db.Model):
    __tablename__ = 'match_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    matches = db.relationship('Match', backref='status', lazy=True)

class TeamInvitationStatus(db.Model):
    __tablename__ = 'team_invitations_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    team_invitations = db.relationship('TeamInvitation', backref='status', lazy=True)

class NotificationType(db.Model):
    __tablename__ = 'notification_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    notifications = db.relationship('Notification', backref='type', lazy=True)

class RelatedEntityType(db.Model):
    __tablename__ = 'related_entity_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationships
    notifications = db.relationship('Notification', backref='related_entity_type', lazy=True)

class ActivityCategory(db.Model):
    __tablename__ = 'activity_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    activities = db.relationship('Activity', backref='category', lazy=True)

# ##############################
# SECCIÓN 2: Tablas Base
# ##############################

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.LargeBinary)  # Compatible with existing auth system
    profile_picture = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        """Initialize user with hash_pass compatibility."""
        from flaskapp.modules.authentication.util import hash_pass
        
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)
    
    @hybrid_property
    def is_system_admin(self):
        """Check if user is system admin."""
        return self.is_admin
    
    def __repr__(self):
        return str(self.name) if self.name else f'<User {self.email}>'

# ##############################
# SECCIÓN 3: Tablas con Dependencias Simples
# ##############################

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_organizations')
    members = db.relationship('OrganizationMember', backref='organization', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='organization', lazy=True, cascade='all, delete-orphan')
    #tournaments = db.relationship('Tournament', backref='organization', lazy=True)
    tournaments = db.relationship(
        'Tournament', 
        back_populates='organization', 
        lazy=True,
        overlaps="event,tournaments"
    )
    
    def __repr__(self):
        return f'<Organization {self.name}, ID: {self.id}>'

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    min_players_per_team = db.Column(db.Integer, nullable=False, default=1)
    category_id = db.Column(db.Integer, db.ForeignKey('activity_categories.id', ondelete='SET NULL'))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('min_players_per_team > 0', name='check_min_players_positive'),
    )
    
    # Relationships
    creator = db.relationship('User', backref='created_activities')
    tournaments = db.relationship('Tournament', backref='activity', lazy=True)
    
    def __repr__(self):
        return f'<Activity {self.name}>'

class OrganizationMember(db.Model):
    __tablename__ = 'organization_members'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    is_organizer = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_organization_user'),
        db.Index('idx_organization_members_organizer', 'organization_id', 'is_organizer'),
    )
    
    # Relationships
    user = db.relationship('User', backref='organization_memberships')
    
    def __repr__(self):
        return f'<OrganizationMember org:{self.organization_id} user:{self.user_id}>'

# ##############################
# SECCIÓN 4: Tablas con Dependencias Complejas
# ##############################

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('event_statuses.id'), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uq_org_event_name'),
        UniqueConstraint('organization_id', 'id', name='uq_org_event_id'),
        CheckConstraint('start_date <= end_date', name='check_dates_order'),
        db.Index('idx_events_dates', 'start_date', 'end_date'),
    )
    
    # Relationships
    creator = db.relationship('User', backref='created_events')
    #tournaments = db.relationship('Tournament', backref='event', lazy=True)
    tournaments = db.relationship(
        'Tournament', 
        back_populates='event', 
        lazy=True, 
        cascade='all, delete-orphan',
        overlaps="event,tournaments"
    )
    
    def __repr__(self):
        return f'<Event {self.name}>'

class Tournament(db.Model):
    __tablename__ = 'tournaments'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='RESTRICT'), nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    max_teams = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    prizes = db.Column(db.Text)
    status_id = db.Column(db.Integer, db.ForeignKey('tournament_statuses.id'), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='check_dates_order'),
        CheckConstraint('max_teams > 0', name='check_max_teams_positive'),
        db.Index('idx_tournaments_dates', 'start_date', 'end_date'),
    )
    
    # Relationships
    creator = db.relationship('User', backref='created_tournaments')
    teams = db.relationship('Team', backref='tournament', lazy=True, cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='tournament', lazy=True, cascade='all, delete-orphan')
    referees = db.relationship('TournamentReferee', backref='tournament', lazy=True, cascade='all, delete-orphan')
    event = db.relationship(
        'Event',
        foreign_keys=[event_id],
        back_populates='tournaments'
    )

    organization = db.relationship(
        'Organization',
        foreign_keys=[organization_id], 
        back_populates='tournaments'
    )
    
    def __repr__(self):
        return f'<Tournament {self.name}>'

class TournamentReferee(db.Model):
    __tablename__ = 'tournament_referees'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tournament_id', 'user_id', name='uq_tournament_referee'),
    )
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='referee_assignments')
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by], backref='referee_assignments_made')
    
    def __repr__(self):
        return f'<TournamentReferee tournament:{self.tournament_id} user:{self.user_id}>'

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    seed_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tournament_id', 'name', name='uq_tournament_team_name'),
        CheckConstraint('seed_score >= 0', name='check_seed_score_not_negative'),
    )
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    invitations = db.relationship('TeamInvitation', backref='team', lazy=True, cascade='all, delete-orphan')
    matches_as_team_a = db.relationship('Match', foreign_keys='Match.team_a_id', backref='team_a', lazy=True)
    matches_as_team_b = db.relationship('Match', foreign_keys='Match.team_b_id', backref='team_b', lazy=True)
    won_matches = db.relationship('Match', foreign_keys='Match.winner_id', backref='winner_team', lazy=True)
    
    def __repr__(self):
        return f'<Team {self.name}>'

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    is_leader = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
        db.Index('idx_team_members_leader', 'team_id', 'is_leader'),
    )
    
    # Relationships
    user = db.relationship('User', backref='team_memberships')
    
    def __repr__(self):
        return f'<TeamMember team:{self.team_id} user:{self.user_id}>'

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 0=final, higher=earlier rounds
    match_number = db.Column(db.Integer, nullable=False)  # Unique position in bracket tree
    team_a_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'))
    team_b_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'))
    score_team_a = db.Column(db.Integer)
    score_team_b = db.Column(db.Integer)
    winner_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'))
    best_player_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    is_bye = db.Column(db.Boolean, default=False)
    status_id = db.Column(db.Integer, db.ForeignKey('match_statuses.id'), nullable=False, index=True)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    recorded_by_referee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tournament_id', 'match_number', name='uq_tournament_match_number'),
        CheckConstraint(
            'winner_id IS NULL OR winner_id = team_a_id OR winner_id = team_b_id',
            name='check_winner_is_participant'
        ),
        CheckConstraint('team_a_id IS DISTINCT FROM team_b_id', name='check_teams_are_distinct'),
        CheckConstraint(
            'NOT is_bye OR (team_a_id IS NOT NULL AND team_b_id IS NULL)',
            name='check_bye_has_only_team_a'
        ),
        CheckConstraint(
            '(score_team_a IS NULL AND score_team_b IS NULL) OR '
            '(score_team_a IS NOT NULL AND score_team_b IS NOT NULL AND score_team_a <> score_team_b)',
            name='check_scores_consistency'
        ),
        db.Index('idx_matches_tournament_level', 'tournament_id', 'level'),
        db.Index('idx_matches_level_number', 'level', 'match_number'),
        db.Index('idx_matches_bye', 'tournament_id', 'is_bye'),
    )
    
    # Relationships
    best_player = db.relationship('User', foreign_keys=[best_player_id], backref='best_player_matches')
    recorded_by_referee = db.relationship('User', foreign_keys=[recorded_by_referee_id], backref='recorded_matches')
    
    def __repr__(self):
        return f'<Match {self.tournament_id}-{self.match_number}>'

class TeamInvitation(db.Model):
    __tablename__ = 'team_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    invited_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey('team_invitations_statuses.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('team_id', 'invited_user_id', name='uq_team_invited_user'),
    )
    
    # Relationships
    invited_by_user = db.relationship('User', foreign_keys=[invited_by_user_id], backref='sent_team_invitations')
    invited_user = db.relationship('User', foreign_keys=[invited_user_id], backref='received_team_invitations')
    
    def __repr__(self):
        return f'<TeamInvitation team:{self.team_id} user:{self.invited_user_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    type_id = db.Column(db.Integer, db.ForeignKey('notification_types.id'), nullable=False, index=True)
    related_entity_type_id = db.Column(db.Integer, db.ForeignKey('related_entity_types.id'), nullable=False)
    related_entity_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.Index('idx_notifications_unread', 'user_id', 'is_read'),
        db.Index('idx_notifications_entity', 'related_entity_type_id', 'related_entity_id'),
    )
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'