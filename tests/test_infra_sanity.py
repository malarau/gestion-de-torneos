import pytest
from sqlalchemy import text
from flaskapp.database.models import User, Organization, Tournament

def test_infrastructure_and_seeding_health(app, db):
    """
    Este test valida que el entorno de pruebas está sano:
    1. Conexión a BD correcta.
    2. Datos de seed cargados (400 usuarios).
    3. Triggers SQL presentes.
    """
    
    # --- 1. VALIDAR CONFIGURACIÓN DE CONEXIÓN ---
    # Verificamos que estamos apuntando al puerto del contenedor de pruebas (5433)
    # y NO al de producción.
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"\n[DEBUG] Conectado a: {db_uri}")
    
    assert '5433' in db_uri, \
        f"ERROR CRÍTICO: El test está intentando conectarse a {db_uri}. Debería ser puerto 5433."

    # --- 2. VALIDAR QUE EL SEED CORRIÓ ---
    # Tu script seed_base_data.sql crea estados, y el seed_db_command crea 400 usuarios.
    # Vamos a contarlos.
    user_count = User.query.count()
    org_count = Organization.query.count()
    
    print(f"[DEBUG] Usuarios encontrados: {user_count}")
    print(f"[DEBUG] Organizaciones encontradas: {org_count}")

    assert user_count > 0, "FALLO: La tabla de usuarios está vacía. El Seed no se ejecutó."
    assert user_count >= 400, f"ADVERTENCIA: Se esperaban 400+ usuarios, hay {user_count}."
    assert org_count > 0, "FALLO: No hay organizaciones creadas."

    # --- 3. VALIDAR QUE PODEMOS ESCRIBIR (ROLLBACK AUTOMÁTICO) ---
    # Intentamos crear un usuario dummy para ver si la BD responde
    email_test = "pytest_check@test.com"
    
    # Paso A: Limpieza preventiva (Si el usuario ya existe de un test anterior, bórralo)
    existing_user = User.query.filter_by(email=email_test).first()
    
    if existing_user:
        db.session.delete(existing_user)
        db.session.commit()
    
    # Paso B: Crear el usuario ahora que sabemos que está limpio
    test_user = User(
        name="Test Pytest User", 
        email=email_test, 
        password="password"
    )
    db.session.add(test_user)
    db.session.commit()
    
    # Verificación final
    check_user = User.query.filter_by(email=email_test).first()
    assert check_user is not None
    
    print("[EXITO] Infraestructura, Seed y Escritura funcionando correctamente.")

def test_triggers_are_loaded(db):
    """
    Valida que los Triggers SQL están cargados en la base de datos de test.
    """
    sql = """
    SELECT event_object_table, trigger_name 
    FROM information_schema.triggers 
    WHERE trigger_name = 'new_match_trigger'
    """
    
    result = db.session.execute(text(sql)).fetchone() 
    
    assert result is not None, "FALLO CRÍTICO: Los Triggers SQL no están cargados."
    assert result[0] == 'matches', "El trigger debería estar asociado a la tabla matches."
    
    print("[EXITO] Los Triggers de PL/pgSQL están cargados y listos.")