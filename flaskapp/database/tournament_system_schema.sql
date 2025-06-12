-- =============================================
-- ARCHIVO: tournament_system_schema.sql
-- DESCRIPCIÓN: Esquema completo para sistema de torneos con eliminación simple
-- =============================================

-- ##############################
-- SECCIÓN 1: Tipos enumerados (status, etc.)
-- ##############################

-- Estados de eventos
CREATE TABLE event_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Estados de torneos
CREATE TABLE tournament_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Estados de partidos
CREATE TABLE match_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Estados de invitaciones a equipos
CREATE TABLE team_invitations_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Tipos de notificaciones
CREATE TABLE notification_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Tipos de entidades relacionadas para notificaciones
CREATE TABLE related_entity_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Categorías de actividades
CREATE TABLE activity_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- ##############################
-- SECCIÓN 2: Tablas base (sin FKs)
-- ##############################

-- Usuarios del sistema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    profile_picture VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- ##############################
-- SECCIÓN 3: Tablas con dependencias simples
-- ##############################

-- Organizaciones (depende de users)
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Actividades/deportes (depende de users y activity_categories)
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    min_players_per_team INTEGER NOT NULL DEFAULT 1,
    category_id INTEGER REFERENCES activity_categories(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT check_min_players_positive 
        CHECK (min_players_per_team > 0)
);

-- Miembros de organizaciones (depende de users y organizations)
CREATE TABLE organization_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    is_organizer BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, user_id)
);

-- ##############################
-- SECCIÓN 4: Tablas con dependencias complejas
-- ##############################

-- Eventos (depende de organizations, event_statuses, users)
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    status_id INTEGER REFERENCES event_statuses(id) NOT NULL,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(organization_id, name),
    UNIQUE(organization_id, id),
    CONSTRAINT check_dates_order
        CHECK (start_date <= end_date)
);

-- Torneos (depende de organizations, events, activities, tournament_statuses, users)
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE RESTRICT,
    event_id INTEGER,
    activity_id INTEGER REFERENCES activities(id) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    max_teams INTEGER NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    prizes TEXT,
    status_id INTEGER REFERENCES tournament_statuses(id) NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT check_dates_order 
        CHECK (start_date <= end_date),
    CONSTRAINT check_max_teams_positive
        CHECK (max_teams > 0),
    FOREIGN KEY (organization_id, event_id)
        REFERENCES events (organization_id, id) ON DELETE RESTRICT
);

-- Árbitros de torneos (depende de tournaments, users)
CREATE TABLE tournament_referees (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id, user_id)
);

-- Equipos (depende de tournaments)
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(100) NOT NULL,
    seed_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(tournament_id, name),
    CONSTRAINT check_seed_score_not_negative
        CHECK (seed_score >= 0)
);

-- Miembros de equipos (depende de teams, users)
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    is_leader BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);

-- Partidos (depende de tournaments, teams, match_statuses, users)
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    level INTEGER NOT NULL, -- Nivel/Ronda en el bracket (ej. 0=final)
    match_number INTEGER NOT NULL, -- Posición única en el árbol del bracket
    team_a_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    team_b_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    score_team_a INTEGER,
    score_team_b INTEGER,
    winner_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    best_player_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_bye BOOLEAN DEFAULT FALSE,
    status_id INTEGER REFERENCES match_statuses(id) NOT NULL,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP,
    recorded_by_referee_id INTEGER REFERENCES users(id),
    UNIQUE(tournament_id, match_number),
    CONSTRAINT check_winner_is_participant
        CHECK (winner_id IS NULL OR winner_id = team_a_id OR winner_id = team_b_id),
    CONSTRAINT check_teams_are_distinct
        CHECK (team_a_id IS DISTINCT FROM team_b_id),
    CONSTRAINT check_bye_has_only_team_a
        CHECK (NOT is_bye OR (team_a_id IS NOT NULL AND team_b_id IS NULL)),
    CONSTRAINT check_scores_consistency
        CHECK (
            (score_team_a IS NULL AND score_team_b IS NULL) OR
            (score_team_a IS NOT NULL AND score_team_b IS NOT NULL AND score_team_a <> score_team_b)
        )
);

-- Invitaciones a equipos (depende de teams, users, team_invitations_statuses)
CREATE TABLE team_invitations (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE NOT NULL,
    invited_by_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    invited_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    status_id INTEGER REFERENCES team_invitations_statuses(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(team_id, invited_user_id)
);

-- Notificaciones (depende de users, notification_types, related_entity_types)
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    type_id INTEGER REFERENCES notification_types(id) NOT NULL,
    related_entity_type_id INTEGER REFERENCES related_entity_types(id) NOT NULL,
    related_entity_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ##############################
-- SECCIÓN 5: Funciones
-- ##############################

-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función principal para manejar resultados de partidos
CREATE OR REPLACE FUNCTION handle_match_result()
RETURNS TRIGGER AS $$
DECLARE
    completed_status_id INTEGER;
    pending_status_id INTEGER;
    next_match RECORD;
BEGIN
    -- Obtener IDs de estados
    SELECT id INTO completed_status_id FROM match_statuses WHERE code = 'completed';
    SELECT id INTO pending_status_id FROM match_statuses WHERE code = 'pending';
    
    -- 1. Auto-completar si se ingresan ambos scores
    IF NEW.score_team_a IS NOT NULL 
       AND NEW.score_team_b IS NOT NULL 
       AND (OLD.status_id IS NULL OR OLD.status_id <> completed_status_id)
    THEN
        NEW.status_id := completed_status_id;
        NEW.completed_at := NOW();
    END IF;
    
    -- 2. Determinar ganador automáticamente al completarse
    IF NEW.status_id = completed_status_id THEN
        -- Caso Bye: ganador automático es team_a
        IF NEW.is_bye THEN
            NEW.winner_id := NEW.team_a_id;
        -- Partido normal: calcular ganador por score
        ELSIF NEW.score_team_a IS NOT NULL AND NEW.score_team_b IS NOT NULL THEN
            IF NEW.score_team_a > NEW.score_team_b THEN
                NEW.winner_id := NEW.team_a_id;
            ELSIF NEW.score_team_b > NEW.score_team_a THEN
                NEW.winner_id := NEW.team_b_id;
            ELSE
                -- Empate (no permitido por constraint, pero por seguridad)
                RAISE EXCEPTION 'No se permiten empates. Debe haber un ganador claro.';
            END IF;
        END IF;
    END IF;
    
    -- 3. Propagación automática al siguiente match (excepto final)
    IF NEW.status_id = completed_status_id 
       AND NEW.winner_id IS NOT NULL 
       AND NEW.level > 0 -- Excluir final (level 0)
    THEN
        -- Calcular posición del siguiente match
        next_match.match_number := CEIL(NEW.match_number / 2.0);
        next_match.level := NEW.level - 1;
        
        -- Determinar posición en el siguiente match
        IF NEW.match_number % 2 = 0 THEN
            -- Posición par -> team_a del siguiente match
            UPDATE matches
            SET team_a_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        ELSE
            -- Posición impar -> team_b del siguiente match
            UPDATE matches
            SET team_b_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para manejar Byes al crear partidos
CREATE OR REPLACE FUNCTION handle_new_match()
RETURNS TRIGGER AS $$
DECLARE
    completed_status_id INTEGER;
BEGIN
    -- Auto-completar Byes al crear partidos
    IF NEW.is_bye THEN
        SELECT id INTO completed_status_id FROM match_statuses WHERE code = 'completed';
        NEW.status_id := completed_status_id;
        NEW.winner_id := NEW.team_a_id;
        NEW.completed_at := NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función de propagación inmediata para Byes
CREATE OR REPLACE FUNCTION propagate_bye_winner()
RETURNS TRIGGER AS $$
DECLARE
    next_match RECORD;
BEGIN
    IF NEW.is_bye AND NEW.winner_id IS NOT NULL AND NEW.level > 0 THEN
        -- Calcular siguiente match
        next_match.match_number := CEIL(NEW.match_number / 2.0);
        next_match.level := NEW.level - 1;
        
        -- Propagación inmediata
        IF NEW.match_number % 2 = 0 THEN
            UPDATE matches
            SET team_a_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        ELSE
            UPDATE matches
            SET team_b_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match.level
              AND match_number = next_match.match_number;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para validar y bloquear edición de matches Bye
CREATE OR REPLACE FUNCTION validate_bye_match()
RETURNS TRIGGER AS $$
DECLARE
    completed_status_id INTEGER;
BEGIN
    -- Obtener ID del estado 'completed'
    SELECT id INTO completed_status_id FROM match_statuses WHERE code = 'completed';
    
    -- Si es Bye, verificar que no se esté modificando incorrectamente
    IF OLD.is_bye THEN
        IF (
            -- Cambios prohibidos en Byes:
            NEW.team_a_id <> OLD.team_a_id OR
            NEW.team_b_id IS NOT NULL OR  -- Bye solo debe tener team_a
            NEW.is_bye = FALSE OR
            NEW.status_id <> completed_status_id OR
            NEW.winner_id <> OLD.team_a_id OR
            (NEW.score_team_a IS NOT NULL OR NEW.score_team_b IS NOT NULL)
        ) THEN
            RAISE EXCEPTION 
                'No se puede modificar un Match Bye. Los Byes son automáticos y no editables. Match ID: %', 
                OLD.id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ##############################
-- SECCIÓN 6: Triggers
-- ##############################

-- Triggers para updated_at automático
CREATE TRIGGER set_timestamp_users
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_organizations
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_activities
    BEFORE UPDATE ON activities
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_events
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_tournaments
    BEFORE UPDATE ON tournaments
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_teams
    BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_matches
    BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_team_invitations
    BEFORE UPDATE ON team_invitations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- Triggers para manejo de partidos
CREATE TRIGGER new_match_trigger
    BEFORE INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_new_match();

CREATE TRIGGER match_result_trigger
    BEFORE INSERT OR UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_match_result();

CREATE TRIGGER bye_propagation_trigger
    AFTER INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION propagate_bye_winner();

CREATE TRIGGER lock_bye_matches
    BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION validate_bye_match();

-- ##############################
-- SECCIÓN 7: Índices de optimización
-- ##############################

-- Índices para tablas principales
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_admin ON users(is_admin) WHERE is_admin = TRUE;
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_activities_name ON activities(name);
CREATE INDEX idx_activities_active ON activities(is_active) WHERE is_active = TRUE;

-- Índices para relaciones frecuentes
CREATE INDEX idx_organization_members_user ON organization_members(user_id);
CREATE INDEX idx_organization_members_org ON organization_members(organization_id);
CREATE INDEX idx_organization_members_organizer ON organization_members(organization_id, is_organizer) WHERE is_organizer = TRUE;
CREATE INDEX idx_tournament_referees_user ON tournament_referees(user_id);
CREATE INDEX idx_tournament_referees_tournament ON tournament_referees(tournament_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_leader ON team_members(team_id, is_leader) WHERE is_leader = TRUE;

-- Índices para búsquedas en torneos y eventos
CREATE INDEX idx_tournaments_organization ON tournaments(organization_id);
CREATE INDEX idx_tournaments_activity ON tournaments(activity_id);
CREATE INDEX idx_tournaments_status ON tournaments(status_id);
CREATE INDEX idx_tournaments_dates ON tournaments(start_date, end_date);
CREATE INDEX idx_events_organization ON events(organization_id);
CREATE INDEX idx_events_status ON events(status_id);
CREATE INDEX idx_events_dates ON events(start_date, end_date);

-- Índices para el sistema de matches (bracket)
CREATE INDEX idx_matches_tournament_level ON matches(tournament_id, level);
CREATE INDEX idx_matches_tournament_status ON matches(tournament_id, status_id);
CREATE INDEX idx_matches_level_number ON matches(level, match_number);
CREATE INDEX idx_matches_team_a ON matches(team_a_id) WHERE team_a_id IS NOT NULL;
CREATE INDEX idx_matches_team_b ON matches(team_b_id) WHERE team_b_id IS NOT NULL;
CREATE INDEX idx_matches_winner ON matches(winner_id) WHERE winner_id IS NOT NULL;
CREATE INDEX idx_matches_bye ON matches(tournament_id, is_bye) WHERE is_bye = TRUE;

-- Índices para notificaciones
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_entity ON notifications(related_entity_type_id, related_entity_id);
CREATE INDEX idx_notifications_type ON notifications(type_id);

-- Índices para invitaciones
CREATE INDEX idx_team_invitations_user ON team_invitations(invited_user_id);
CREATE INDEX idx_team_invitations_team ON team_invitations(team_id);
CREATE INDEX idx_team_invitations_status ON team_invitations(status_id);