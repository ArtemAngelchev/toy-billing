# -*- coding: utf-8 -*-
import logging

import pytest
from _pytest.logging import caplog as _caplog
from _pytest.monkeypatch import MonkeyPatch
from alembic.command import downgrade, upgrade
from alembic.config import Config as AlembicConfig
from loguru import logger

from config import CONFIG
from src import create_app


@pytest.fixture
def caplog(_caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropogateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)


@pytest.fixture(scope='session')
def monkeypatch_session():
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope='session', autouse=True)
def patch_session_envs(monkeypatch_session):
    # pylint: disable=redefined-outer-name
    monkeypatch_session.setattr(CONFIG, 'LOG_LEVEL', 'DEBUG')
    monkeypatch_session.setattr(CONFIG, 'LOG_CONSOLE_HANDLER', True)
    monkeypatch_session.setattr(CONFIG, 'LOG_FILE_HANDLER', True)

    monkeypatch_session.setattr(CONFIG, 'SQLALCHEMY_ECHO', False)
    monkeypatch_session.setattr(
        CONFIG, 'SQLALCHEMY_DATABASE_URI', (
            'postgresql://local:local@postgres:5432/local'
            '?application_name=billing-unittests'
        )
    )

    monkeypatch_session.setenv('FLASK_ENV', 'production')
    monkeypatch_session.setenv('PYTHONUNBUFFERED', '1')


@pytest.fixture
def current_app():
    yield create_app()


@pytest.fixture(autouse=True)
def prepare_db(current_app):  # pylint: disable=redefined-outer-name
    config = AlembicConfig('migrations/alembic-unittest.ini')

    with current_app.app_context():
        upgrade(config, 'head')
        yield
        downgrade(config, 'base')


@pytest.fixture
def client(current_app):  # pylint: disable=redefined-outer-name
    with current_app.test_client() as _client:
        yield _client
