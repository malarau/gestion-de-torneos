-- =============================================
-- ARCHIVO: seed_base_data.sql
-- DESCRIPCIÓN: Datos base requeridos para el funcionamiento del sistema
-- FECHA: 2025-06-09
-- =============================================

-- ##############################
-- SECCIÓN 1: Funciones
-- ##############################

-- Función para manejar Byes al crear partidos

-- Función: trigger_set_timestamp()
-- Descripción: Actualiza automáticamente el campo updated_at al hacer UPDATE
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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
        SELECT CEILING(NEW.match_number / 2.0)::INTEGER INTO next_match_match_number;
        next_match_level := NEW.level - 1;

        -- Propagación inmediata
        IF MOD(NEW.match_number, 2) = 0 THEN
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

-- Función para enviar notificaciones
CREATE OR REPLACE FUNCTION send_notification(
    user_id INTEGER,
    title TEXT,
    message TEXT,
    type_code TEXT,
    related_entity_type_code TEXT,
    related_entity_id INTEGER
)
RETURNS VOID AS $$
DECLARE
    type_id INTEGER;
    related_entity_type_id INTEGER;
BEGIN
    -- Obtener el ID del tipo de notificación
    SELECT id INTO type_id FROM notification_types WHERE code = type_code;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Notification type % not found', type_code;
    END IF;

    -- Obtener el ID del tipo de entidad relacionada
    SELECT id INTO related_entity_type_id FROM related_entity_types WHERE name = related_entity_type_code;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Related entity type % not found', related_entity_type_code;
    END IF;

    -- Insertar la notificación
    INSERT INTO notifications (user_id, title, message, type_id, related_entity_type_id, related_entity_id, created_at)
    VALUES (user_id, title, message, type_id, related_entity_type_id, related_entity_id, NOW());
END;
$$ LANGUAGE plpgsql;

-- Función para notificar invitaciones de equipos
CREATE OR REPLACE FUNCTION notify_team_invitation()
RETURNS TRIGGER AS $$
DECLARE
    team_name TEXT;
BEGIN
    -- Obtener el nombre del equipo
    SELECT name INTO team_name FROM teams WHERE id = NEW.team_id;

    -- Enviar notificación al usuario invitado
    PERFORM send_notification(
        NEW.invited_user_id,
        'Invitación a equipo',
        'Has sido invitado al equipo: ' || team_name,
        'TEAM_INVITE',
        'TOURNAMENT',
        -- selecting the tournament_id from the team
        (SELECT tournament_id FROM teams WHERE id = NEW.team_id)
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para notificar cuando el torneo cambia a "EN CURSO"
CREATE OR REPLACE FUNCTION notify_tournament_in_progress()
RETURNS TRIGGER AS $$
DECLARE
    tournament_name TEXT;
    in_progress_id INTEGER;
BEGIN
    -- Obtener el ID del estado IN_PROGRESS
    SELECT id INTO in_progress_id FROM tournament_statuses WHERE code = 'IN_PROGRESS';

    -- Verificar si el torneo cambió a estado IN_PROGRESS
    IF NEW.status_id = in_progress_id THEN
        -- Obtener el nombre del torneo
        SELECT name INTO tournament_name FROM tournaments WHERE id = NEW.id;

        -- Enviar notificación a todos los usuarios del torneo
        INSERT INTO notifications (user_id, title, message,is_read, type_id, related_entity_type_id, related_entity_id,created_at)
        SELECT tm.user_id,
            'Torneo iniciado',
            '¡El torneo ' || tournament_name || ' ha comenzado!',
            false,
            (SELECT id FROM notification_types WHERE code = 'TOURNAMENT_START'),
            (SELECT id FROM related_entity_types WHERE name = 'TOURNAMENT'),
            NEW.id,
            NOW()
        FROM teams te
        JOIN tournaments t ON te.tournament_id = t.id
        JOIN team_members tm ON te.id = tm.team_id
        WHERE te.tournament_id = NEW.id;
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

-- Crear triggers para timestamps
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

-- Eliminar triggers relacionados con lógica del sistema
DROP TRIGGER IF EXISTS new_match_trigger ON matches;
DROP TRIGGER IF EXISTS bye_propagation_trigger ON matches;
DROP TRIGGER IF EXISTS notify_team_invitation_trigger ON team_invitations;
DROP TRIGGER IF EXISTS notify_tournament_in_progress ON tournaments;

-- Crear triggers funcionales
CREATE TRIGGER new_match_trigger
    BEFORE INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_new_match();

CREATE TRIGGER bye_propagation_trigger
    AFTER INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION propagate_bye_winner();

CREATE TRIGGER notify_team_invitation_trigger
    AFTER INSERT ON team_invitations
    FOR EACH ROW EXECUTE FUNCTION notify_team_invitation();

CREATE TRIGGER notify_tournament_in_progress
    AFTER UPDATE OF status_id ON tournaments
    FOR EACH ROW
    EXECUTE FUNCTION notify_tournament_in_progress();
