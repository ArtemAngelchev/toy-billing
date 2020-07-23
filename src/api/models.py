# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional
from uuid import UUID as _UUID
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

from src.extensions import db


class OperationModel(db.Model):
    # pylint: disable=no-member
    __tablename__ = 'operations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    transaction = db.Column(
        UUID(as_uuid=True),
        default=uuid4,
        nullable=False,
        index=True,
    )
    wallet_id = db.Column(
        db.Integer,
        ForeignKey('wallets.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True,
    )
    amount_was = db.Column(db.Integer, nullable=False)
    amount_become = db.Column(db.Integer, nullable=False)
    operation_amount = db.Column(db.Integer, nullable=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)


class WalletModel(db.Model):
    # pylint: disable=no-member
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    amount = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(
        db.Integer,
        ForeignKey('customers.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True,
    )
    operations = relationship(
        'OperationModel',
        cascade='all, delete-orphan',
        backref='wallet',
    )


class CustomerModel(db.Model):  # type: ignore
    # pylint: disable=no-member
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = \
        db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)
    deleted = db.Column(db.Boolean, default=False, nullable=False)

    wallet = relationship(
        'WalletModel',
        cascade='all, delete-orphan',
        backref='customer',
        uselist=False,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wallet = WalletModel(amount=0)


def register_operation(
        wallet_id: int,
        amount_was: int,
        amount_become: int,
        amount: int,
        transaction: Optional[_UUID] = None,
) -> _UUID:
    # pylint: disable=no-member
    transaction = transaction if transaction else uuid4()
    operation = OperationModel(
        transaction=transaction,
        wallet_id=wallet_id,
        amount_was=amount_was,
        amount_become=amount_become,
        operation_amount=amount,
    )
    db.session.add(operation)
    return transaction
