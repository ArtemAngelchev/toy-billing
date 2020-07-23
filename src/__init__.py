# -*- coding: utf-8 -*-
import sys
from uuid import uuid4

import status
from flask import Flask, request
from flask_compress import Compress
from loguru import logger
from pydantic import ValidationError

from config import CONFIG

from .api import blueprints
from .exceptions import RecipientNotExistError, SenderNotEnoughMoneyError
from .extensions import db, migrate


def init_logger():

    def patcher(record):
        try:
            record['extra'].update(request_id=request.id)
        except Exception:  # pylint: disable=broad-except
            ...

    console = {
        'sink': sys.stderr,
        'format': (
            '<level>{level}</level> '
            '<green>{time: YYYY-MM-DD HH:mm:ss}</green> '
            '{message} | {extra}'
        ),
        'colorize': True,
        'level': CONFIG.LOG_LEVEL,
    }
    _file = {
        'sink': '/var/log/billing.log',
        'backtrace': True,
        'serialize': True,
        'diagnose': True,
        'retention': '5 days',
        'level': CONFIG.LOG_LEVEL,
    }
    log_config = {
        'handlers': (
            [_file][:CONFIG.LOG_FILE_HANDLER] +
            [console][:CONFIG.LOG_CONSOLE_HANDLER]
        ),
        'patcher': patcher,
    }
    logger.configure(**log_config)


def create_app() -> Flask:
    init_logger()
    logger.info('Service running.')

    app = Flask(__name__.split('.')[0])
    app.config.from_object(CONFIG)

    Compress(app)

    db.init_app(app)
    migrate.init_app(app, db)

    register_request_id(app)
    register_common_exceptions(app)

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    return app


def register_request_id(app: Flask):
    def set_request_id():
        _id = request.headers.get('x-request-id')
        request.id = f'outer-{_id}' if _id else f'inner-{uuid4().hex}'

    app.before_request(set_request_id)


def error400(exc):
    return (
        {'status': 'error', 'message': exc.errors()},
        status.HTTP_400_BAD_REQUEST,
    )


def error404(_):
    return (
        {'status': 'error', 'message': 'Resource not found.'},
        status.HTTP_404_NOT_FOUND,
    )


def error405(_):
    return (
        {'status': 'error', 'message': 'Method not allowed.'},
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )


def error500(_):
    logger.exception('Some unexpected error occured')

    _id = str()
    try:
        _id = f' Error id: {request.id}'
    except Exception:  # pylint: disable=broad-except
        ...

    return (
        {
            'status': 'error',
            'message': f'Something went wrong.{_id}',
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_common_exceptions(app: Flask):
    app.register_error_handler(ValidationError, error400)
    app.register_error_handler(SenderNotEnoughMoneyError, error400)
    app.register_error_handler(RecipientNotExistError, error400)
    app.register_error_handler(status.HTTP_404_NOT_FOUND, error404)
    app.register_error_handler(status.HTTP_405_METHOD_NOT_ALLOWED, error405)
    app.register_error_handler(Exception, error500)
