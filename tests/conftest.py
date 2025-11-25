import pytest
from flaskapp import create_app, db as _db
from flaskapp.config import TestingConfig 

@pytest.fixture(scope='session')
def app():
    # AHORA SÍ FUNCIONA: Le pasamos la configuración explícitamente
    # Esto hará que create_app use el puerto 5433 y cargue los triggers
    app = create_app(config_class=TestingConfig)
    
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    yield _db