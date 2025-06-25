-- =============================================
-- ARCHIVO: seed_base_data.sql
-- DESCRIPCIÓN: Datos base requeridos para el funcionamiento del sistema
-- FECHA: 2025-06-09
-- =============================================

-- ##############################
-- SECCIÓN 1: Funciones
-- ##############################

CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
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
        SELECT id INTO completed_status_id FROM match_statuses WHERE code = 'COMPLETED';
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
    next_match_match_number INTEGER;
    next_match_level INTEGER;
BEGIN
    IF NEW.is_bye AND NEW.winner_id IS NOT NULL AND NEW.level > 0 THEN
        -- Calcular siguiente match
        next_match_match_number := CEIL(NEW.match_number / 2.0);
        next_match_level := NEW.level - 1;
        
        -- Propagación inmediata
        IF NEW.match_number % 2 = 0 THEN
            UPDATE matches
            SET team_a_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match_level
              AND match_number = next_match_match_number;
        ELSE
            UPDATE matches
            SET team_b_id = NEW.winner_id,
                updated_at = NOW()
            WHERE tournament_id = NEW.tournament_id
              AND level = next_match_level
              AND match_number = next_match_match_number;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ##############################
-- SECCIÓN 2: Triggers
-- ##############################

-- Eliminar triggers existentes si ya existen
DROP TRIGGER IF EXISTS set_timestamp_users ON users;
DROP TRIGGER IF EXISTS set_timestamp_organizations ON organizations;
DROP TRIGGER IF EXISTS set_timestamp_activities ON activities;
DROP TRIGGER IF EXISTS set_timestamp_events ON events;
DROP TRIGGER IF EXISTS set_timestamp_tournaments ON tournaments;
DROP TRIGGER IF EXISTS set_timestamp_teams ON teams;
DROP TRIGGER IF EXISTS set_timestamp_matches ON matches;
DROP TRIGGER IF EXISTS set_timestamp_team_invitations ON team_invitations;

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

-- Elimina los triggers si ya existen
DROP TRIGGER IF EXISTS new_match_trigger ON matches;
DROP TRIGGER IF EXISTS match_result_trigger ON matches;
DROP TRIGGER IF EXISTS bye_propagation_trigger ON matches;

CREATE TRIGGER new_match_trigger
    BEFORE INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_new_match();

CREATE TRIGGER bye_propagation_trigger
    AFTER INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION propagate_bye_winner();