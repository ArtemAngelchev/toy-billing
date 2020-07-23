# -*- coding: utf-8 -*-
from functools import wraps

from flask import request
from pydantic import BaseModel, Field, conint, constr, root_validator


def validate(schema: BaseModel):
    def closure(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = schema(**(request.get_json(silent=True) or dict())).dict()
            request.valid_json = data
            return func(*args, **kwargs)
        return wrapper
    return closure


class CustomerSchema(BaseModel):
    name: str

    class Config:
        extra = 'forbid'


class ReplenishmentSchema(BaseModel):
    amount: int = Field(..., ge=1)

    class Config:
        extra = 'forbid'


class TransferSchema(BaseModel):
    customer_id: int
    amount: int = Field(..., ge=1)

    class Config:
        extra = 'forbid'
