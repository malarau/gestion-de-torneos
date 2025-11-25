import pytest
import random
from sqlalchemy.sql.expression import func
from flaskapp.modules.tournaments.service import TournamentService
from flaskapp.modules.matches.service import MatchService
from flaskapp.database.models import Tournament, Match, TournamentReferee, TournamentStatus, MatchStatus, User, TeamMember


import pytest
from flaskapp.modules.tournaments.service import TournamentService
from flaskapp.database.models import Tournament, Match, TournamentStatus, MatchStatus, Team

def test_cp006_validate_bye_trigger_logic(app, db):
    """
    CP-006: Validación de Byes Automáticos (HU-13).
    Escenario: Torneo con 3 equipos (no potencia de 2).
    
    Flujo:
    1. Preparar un torneo con 3 equipos.
    2. Iniciar torneo.
    3. VALIDAR:
       - Se generó un partido marcado como is_bye=True.
       - El Trigger de SQL 'handle_new_match' lo marcó automáticamente como COMPLETED.
       - El Trigger asignó winner_id automáticamente.
    """
    
    # --- 1. PREPARACIÓN (ARRANGE) ---
    reg_open_status = TournamentStatus.query.filter_by(code='REGISTRATION_OPEN').first()
    
    # Buscamos un torneo que tenga al menos 3 equipos
    # (Idealmente uno de 4 para borrarle uno y dejarlo impar)
    tournament = None
    candidates = Tournament.query.filter_by(status_id=reg_open_status.id).all()
    
    for t in candidates:
        if len(t.teams) >= 3:
            tournament = t
            break
            
    if not tournament:
        pytest.skip("No se encontró torneo para manipular equipos.")

    # MANIPULACIÓN DE DATOS: Forzamos que sea impar (3 equipos)
    # Si tiene más de 3, borramos el excedente hasta dejar 3
    current_teams = tournament.teams
    if len(current_teams) > 3:
        # Borramos equipos sobrantes para el test
        teams_to_remove = current_teams[3:]
        for team in teams_to_remove:
            db.session.delete(team)
        db.session.commit()
        print(f"\n[TEST] Se ajustó el torneo {tournament.id} a 3 equipos para forzar Byes.")
    
    # Verificación de precondición
    assert len(tournament.teams) == 3, "El torneo debe tener 3 equipos para generar Byes."

    # --- 2. EJECUCIÓN (ACT) ---
    # Iniciamos el torneo. 
    # Python calculará: 3 equipos -> Bracket de 4. 
    # Ronda 1: 1 Partido Normal (2 vs 3) + 1 Bye (1 vs Nadie).
    TournamentService.start_tournament(tournament.id)

    # --- 3. VALIDACIÓN (ASSERT) ---
    
    # A. Buscar el partido Bye
    bye_match = Match.query.filter_by(
        tournament_id=tournament.id, 
        is_bye=True
    ).first()
    
    assert bye_match is not None, "FALLO: El sistema no generó ningún Bye para 3 equipos."
    
    print(f"[TEST] Bye Match encontrado: ID {bye_match.id} (Nivel {bye_match.level})")

    # B. Validar Trigger de SQL (handle_new_match)
    # El trigger debió actuar INMEDIATAMENTE al insertarse el match
    
    # 1. Estado Completado
    completed_status = MatchStatus.query.filter_by(code='COMPLETED').first()
    assert bye_match.status_id == completed_status.id, \
        "FALLO TRIGGER: El match Bye debería estar COMPLETED automáticamente."
    
    # 2. Ganador Asignado
    assert bye_match.winner_id is not None, \
        "FALLO TRIGGER: El match Bye no tiene ganador asignado."
        
    assert bye_match.winner_id == bye_match.team_a_id, \
        "FALLO TRIGGER: En un Bye, el Team A gana automáticamente."
        
    # 3. Validar que NO tiene oponente
    assert bye_match.team_b_id is None, \
        "Un match Bye no debería tener equipo B."

    print("[EXITO] CP-006: Generación de Byes (Python) y Resolución Automática (SQL Trigger) funcionando.")

def test_cp009_match_propagation_via_service(app, db):
    """
    CP-009: Validar flujo de partido y propagación (HU-25).
    Selecciona un partido real (no Bye) de la base del bracket, 
    juega el partido, asigna un MVP válido y verifica que el ganador avanza.
    """
    
    # --- 1. PREPARACIÓN (ARRANGE) ---
    # Buscamos torneo apto (mismo filtro de siempre)
    reg_open_status = TournamentStatus.query.filter_by(code='REGISTRATION_OPEN').first()
    tournament = None
    candidates = Tournament.query.filter_by(status_id=reg_open_status.id).all()
    for t in candidates:
        if len(t.teams) >= 4:
            tournament = t
            break
            
    if not tournament:
        pytest.skip("No se encontró torneo con 4+ equipos.")

    # Iniciamos torneo para crear el árbol completo
    TournamentService.start_tournament(tournament.id)
    
    # Buscamos el nivel más bajo (donde están los partidos iniciales)
    matches = Match.query.filter_by(tournament_id=tournament.id).all()
    max_level = max(m.level for m in matches)
    
    # --- MEJORA: SELECCIÓN ROBUSTA DE PARTIDO ---
    # Obtenemos matches iniciales que NO son bye y tienen AMBOS equipos asignados
    non_bye_matches = Match.query.filter(
        Match.tournament_id == tournament.id,
        Match.level == max_level,
        Match.is_bye == False,
        Match.team_a_id.isnot(None),
        Match.team_b_id.isnot(None)
    ).all()

    if non_bye_matches:
        match_to_play = random.choice(non_bye_matches)
    else:
        pytest.skip("No se encontraron partidos jugables (No-Bye) en la primera ronda.")

    print(f"\n[TEST] Jugando Match ID {match_to_play.id} (Nivel {match_to_play.level}, # {match_to_play.match_number})")
    print(f"[TEST] {match_to_play.team_a.name} vs {match_to_play.team_b.name}")

    # --- 2. EJECUCIÓN (ACT) ---
    # Simulamos datos del Árbitro
    # Todos los árbitros del torneo
    user_referee = User.query.join(
        TournamentReferee, 
        TournamentReferee.user_id == User.id  # ← EXPLÍCITO
    ).filter(
        TournamentReferee.tournament_id == tournament.id
    ).first()
    
    # --- MVP ---
    # Seleccionamos un MVP del equipo ganador (Team A en este caso)
    mvp_user = User.query.join(TeamMember).filter(
        (TeamMember.team_id == match_to_play.team_a_id)
    ).order_by(func.random()).first()

    if not mvp_user:
        mvp_user = User.query.first() # Fallback por seguridad

    update_data = {
        'user_id': user_referee.id,
        'score_team_a': 3, # Gana A
        'score_team_b': 0,
        'best_player_id': mvp_user.id,
        'recorded_by_referee_id': user_referee.id
    }
    
    # Llamada al Servicio Python
    success = MatchService.update_match(match_to_play.id, update_data)
    
    # --- 3. VALIDACIÓN (ASSERT) ---
    assert success is True
    
    db.session.expire_all()
    updated_match = Match.query.get(match_to_play.id)
    
    # Validar Estado y Ganador
    completed_status = MatchStatus.query.filter_by(code='COMPLETED').first()
    assert updated_match.status_id == completed_status.id
    assert updated_match.winner_id == updated_match.team_a_id
    assert updated_match.best_player_id == mvp_user.id
    
    # Validar Propagación (Matemática del Árbol)
    # No válido para la final (match_number = 1)
    if updated_match.match_number != 1:
        expected_next_number = updated_match.match_number // 2
        expected_next_level = updated_match.level - 1
        
        next_match = Match.query.filter_by(
            tournament_id=tournament.id,
            level=expected_next_level,
            match_number=expected_next_number
        ).first()

        print(f"[TEST] Verificando existencia de Match siguiente (Nivel {expected_next_level}, # {expected_next_number})")
       
        # Como el árbol ya existe, next_match DEBE existir (no ser None)
        assert next_match is not None, "Error de integridad: El árbol del torneo está incompleto."
    
        print(f"[TEST] Verificando propagación hacia Match # {next_match.match_number}")
        
        if updated_match.match_number % 2 == 0:
            # Par -> Slot A
            assert next_match.team_a_id == updated_match.winner_id
        else:
            # Impar -> Slot B
            assert next_match.team_b_id == updated_match.winner_id

        print("[EXITO] CP-009: Lógica de propagación validada correctamente.")
    else:
        print("[INFO] Partido final jugado; no se requiere propagación.")


def test_cp010_validate_no_draws_rule(app, db):
    """
    CP-010: Validación de Regla de Negocio (HU-25).
    Intenta registrar un empate en un partido de eliminación directa.
    El sistema debe rechazar la operación para proteger la integridad del bracket.
    """
    
    # --- 1. PREPARACIÓN (ARRANGE) ---
    # Buscamos torneo apto (mismo filtro robusto de siempre)
    reg_open_status = TournamentStatus.query.filter_by(code='REGISTRATION_OPEN').first()
    tournament = None
    # Solo necesitamos 2 equipos mínimo para tener 1 partido jugable
    candidates = Tournament.query.filter_by(status_id=reg_open_status.id).all()
    for t in candidates:
        if len(t.teams) >= 2:
            tournament = t
            break
            
    if not tournament:
        pytest.skip("No se encontró torneo apto para la prueba.")

    # Iniciamos torneo
    TournamentService.start_tournament(tournament.id)
    
    # Buscamos cualquier partido activo (No Bye)
    match_to_play = Match.query.filter(
        Match.tournament_id == tournament.id,
        Match.is_bye == False,
        Match.team_a_id.isnot(None),
        Match.team_b_id.isnot(None)
    ).first()

    if not match_to_play:
        pytest.skip("No se encontraron partidos jugables.")

    print(f"\n[TEST] Intentando forzar empate en Match ID {match_to_play.id}")

    # --- 2. EJECUCIÓN (ACT) ---
    # Buscamos un árbitro válido (Usando tu corrección del JOIN explícito)
    user_referee = User.query.join(
        TournamentReferee, 
        TournamentReferee.user_id == User.id
    ).filter(
        TournamentReferee.tournament_id == tournament.id
    ).first()

    # Si no hay árbitro asignado en el seed, usamos un admin como fallback (superusuario)
    if not user_referee:
        user_referee = User.query.filter_by(is_admin=True).first()

    # Intentamos registrar un EMPATE (2 vs 2)
    update_data = {
        'user_id': user_referee.id,
        'score_team_a': 2,
        'score_team_b': 2, # <--- EMPATE
        'best_player_id': None, # Irrelevante para el fallo esperado
        'recorded_by_referee_id': user_referee.id
    }
    
    # Llamada al Servicio
    # En tu código, el servicio captura el ValueError y retorna False.
    success = MatchService.update_match(match_to_play.id, update_data)
    
    # --- 3. VALIDACIÓN (ASSERT) ---
    
    # A. El servicio debe indicar fallo
    assert success is False, "El sistema permitió registrar un empate, lo cual es fatal para el bracket."
    
    # Refrescamos datos de la BD para asegurar que no se guardó basura
    db.session.expire_all()
    reloaded_match = Match.query.get(match_to_play.id)
    
    # B. El estado NO debe ser COMPLETED
    completed_status = MatchStatus.query.filter_by(code='COMPLETED').first()
    assert reloaded_match.status_id != completed_status.id, \
        "El partido se marcó como completado a pesar del empate."
        
    # C. No debe haber ganador
    assert reloaded_match.winner_id is None, \
        "El sistema asignó un ganador arbitrario en un empate."
        
    # D. Validar que NO hubo propagación (El siguiente partido sigue vacío)
    if reloaded_match.level > 0:
        next_number = reloaded_match.match_number // 2
        next_level = reloaded_match.level - 1
        
        next_match = Match.query.filter_by(
            tournament_id=tournament.id,
            level=next_level,
            match_number=next_number
        ).first()
        
        # Verificamos el slot correspondiente
        if reloaded_match.match_number % 2 == 0:
            target_slot = next_match.team_a_id
        else:
            target_slot = next_match.team_b_id
            
        assert target_slot is None, "Error Crítico: El empate se propagó al siguiente partido."

    print("[EXITO] CP-010: El sistema rechazó correctamente el empate (Integridad de Bracket asegurada).")