-- =============================================
-- ARCHIVO: seed_base_data.sql
-- DESCRIPCIÓN: Datos base requeridos para el funcionamiento del sistema
-- FECHA: 2025-06-09
-- =============================================

-- ##############################
-- SECCIÓN 1: Funciones
-- ##############################

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

-- Función para enviar notificaciones de invitaciones a equipos
/* 

    type_id = db.Column(db.Integer, db.ForeignKey('notification_types.id'), nullable=False, index=True)
    NotificationType = TEAM_INVITE

    related_entity_type_id = db.Column(db.Integer, db.ForeignKey('related_entity_types.id'), nullable=False)
    RelatedEntityType = TOURNAMENT

    related_entity_id = db.Column(db.Integer, nullable=False)
    related_entity = Id del torneo al que pertenece el equipo que invita al usuario

 */

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
    SELECT id INTO related_entity_type_id FROM related_entity_types WHERE code = related_entity_type_code;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Related entity type % not found', related_entity_type_code;
    END IF; 
    -- Insertar la notificación
    INSERT INTO notifications (user_id, title, message, type_id, related_entity_type_id, related_entity_id)
    VALUES (user_id, title, message, type_id, related_entity_type_id, related_entity_id);
END;
$$ LANGUAGE plpgsql;

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
        NEW.tournament_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Función para enviar notificación cuando el estado del torneo cambia a IN_PROGRESS
CREATE OR REPLACE FUNCTION notify_tournament_in_progress()
RETURNS TRIGGER AS $$
DECLARE
    tournament_name TEXT;
BEGIN
    -- Obtener el nombre del torneo
    SELECT name INTO tournament_name FROM tournaments WHERE id = NEW.tournament_id;
    -- Enviar notificación a todos los usuarios del torneo
    INSERT INTO notifications (user_id, title, message, type_id, related_entity_type_id, related_entity_id)
    SELECT user_id,
           'Torneo iniciado',
           '¡El torneo ' || tournament_name || ' ha comenzado!',
           (SELECT id FROM notification_types WHERE code = 'TOURNAMENT_START'),
           (SELECT id FROM related_entity_types WHERE code = 'TOURNAMENT'),
           NEW.tournament_id
    FROM tournament_users
    WHERE tournament_id = NEW.tournament_id;
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
DROP TRIGGER IF EXISTS notify_team_invitation_trigger ON team_invitations;
DROP TRIGGER IF EXISTS notify_tournament_in_progress ON tournaments;

CREATE TRIGGER notify_tournament_in_progress
    AFTER UPDATE OF status_id ON tournaments
    FOR EACH ROW WHEN (NEW.status_id = (SELECT id FROM tournament_statuses WHERE code = 'IN_PROGRESS'))
    EXECUTE FUNCTION notify_tournament_in_progress();

CREATE TRIGGER new_match_trigger
    BEFORE INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION handle_new_match();

CREATE TRIGGER bye_propagation_trigger
    AFTER INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION propagate_bye_winner();

CREATE TRIGGER notify_team_invitation_trigger
    AFTER INSERT ON team_invitations
    FOR EACH ROW EXECUTE FUNCTION notify_team_invitation();