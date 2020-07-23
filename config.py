# -*- coding: utf-8 -*-
from pydantic import BaseSettings


class Config(BaseSettings):
    JSON_AS_ASCII: bool
    JSONIFY_PRETTYPRINT_REGULAR: bool
    JSON_SORT_KEYS: bool

    ZLIB_COMP_LEVEL: int

    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False

    LOG_LEVEL: str
    LOG_CONSOLE_HANDLER: bool
    LOG_FILE_HANDLER: bool


CONFIG = Config()
