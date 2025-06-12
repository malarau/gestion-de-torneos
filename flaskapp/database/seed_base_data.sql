-- =============================================
-- ARCHIVO: seed_base_data.sql
-- DESCRIPCIÓN: Datos base requeridos para el funcionamiento del sistema
-- FECHA: 2025-06-09
-- =============================================

-- ##############################
-- SECCIÓN 1: Funciones
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
-- SECCIÓN 2: Triggers
-- ##############################

-- Triggers para updated_at automático
CREATE OR REPLACE TRIGGER set_timestamp_users
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE OR REPLACE TRIGGER set_timestamp_organizations
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE OR REPLACE TRIGGER set_timestamp_activities
    BEFORE UPDATE ON activities
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE OR REPLACE TRIGGER set_timestamp_events
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE OR REPLACE TRIGGER set_timestamp_tournaments
    BEFORE UPDATE ON tournaments
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE OR REPLACE TRIGGER set_timestamp_teams
    BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE OR REPLACE TRIGGER set_timestamp_matches
    BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE OR REPLACE TRIGGER set_timestamp_team_invitations
    BEFORE UPDATE ON team_invitations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- Triggers para manejo de partidos
CREATE OR REPLACE TRIGGER new_match_trigger
    BEFORE INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_new_match();

CREATE OR REPLACE TRIGGER match_result_trigger
    BEFORE INSERT OR UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_match_result();

CREATE OR REPLACE TRIGGER bye_propagation_trigger
    AFTER INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION propagate_bye_winner();

CREATE OR REPLACE TRIGGER lock_bye_matches
    BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION validate_bye_match();