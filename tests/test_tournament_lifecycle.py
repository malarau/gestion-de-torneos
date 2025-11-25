import pytest
from flaskapp.database.models import Tournament, Match, Team, MatchStatus

import pytest
from flaskapp.modules.tournaments.service import TournamentService
from flaskapp.database.models import Tournament, Match, TournamentStatus, MatchStatus

def test_cp005_start_tournament_service_integration(app, db):
    """
    CP-005: Validar inicio de torneo VÍA SERVICIO.
    Verifica que al llamar a TournamentService.start_tournament:
    1. El estado cambia a IN_PROGRESS.
    2. Se generan los registros en la tabla matches.
    3. Los triggers de DB actúan sobre los Byes (si aplica).
    """
    
    # --- 1. PREPARACIÓN (ARRANGE) ---
    # Buscamos un torneo 'REGISTRATION_OPEN' que tenga equipos (del seed)
    # El seed debe crear torneos en estado REGISTRATION_OPEN, no solo PENDING.
    
    # Primero, necesitamos saber el ID del estado 'REGISTRATION_OPEN'
    reg_open_status = TournamentStatus.query.filter_by(code='REGISTRATION_OPEN').first()
    
    # Buscamos un torneo apto
    tournament = None
    candidates = Tournament.query.filter_by(status_id=reg_open_status.id).all()
    
    for t in candidates:
        if len(t.teams) >= 2: # Requisito del servicio
            tournament = t
            break
            
    if not tournament:
        pytest.skip("No se encontraron torneos en estado REGISTRATION_OPEN con equipos en el seed.")

    print(f"\n[TEST] Probando con Torneo ID: {tournament.id} - Equipos: {len(tournament.teams)}")
    initial_match_count = len(tournament.matches)
    assert initial_match_count == 0, "El torneo no debería tener partidos antes de iniciar."

    # --- 2. EJECUCIÓN (ACT) ---
    # Llamamos al servicio real, tal como lo hace routes.py
    success = TournamentService.start_tournament(tournament.id)

    # --- 3. VERIFICACIÓN (ASSERT) ---
    assert success is True

    # Refrescamos el objeto desde la BD para ver los cambios confirmados
    db.session.expire(tournament)
    
    # A. Validar cambio de estado
    in_progress_status = TournamentStatus.query.filter_by(code='IN_PROGRESS').first()
    assert tournament.status_id == in_progress_status.id, \
        f"El estado debería ser IN_PROGRESS (ID {in_progress_status.id}), pero es {tournament.status_id}"

    # B. Validar generación de Brackets (Lógica de Python)
    matches = Match.query.filter_by(tournament_id=tournament.id).all()
    match_count = len(matches)
    print(f"[TEST] Partidos generados: {match_count}")
    
    assert match_count > 0, "El servicio debió generar partidos en la BD"
    
    # C. Validar Integración con Triggers SQL (Lógica Híbrida)
    # Buscamos si hubo algún Bye. Si lo hubo, el Trigger debió completarlo.
    bye_match = Match.query.filter_by(tournament_id=tournament.id, is_bye=True).first()
    
    if bye_match:
        # Aquí probamos que tu archivo SQL (handle_new_match) funcionó
        completed_status = MatchStatus.query.filter_by(code='COMPLETED').first()
        print(f"[TEST] Validando Trigger de Bye en Match {bye_match.match_number}...")
        
        assert bye_match.status_id == completed_status.id, \
            "FALLO DE TRIGGER: El match Bye debería estar COMPLETED automáticamente."
        assert bye_match.winner_id == bye_match.team_a_id, \
            "FALLO DE TRIGGER: El match Bye debería tener ganador asignado."
            
    print("[EXITO] CP-005: Servicio de inicio y Triggers de DB validados correctamente.")
