# -*- coding: utf-8 -*-
from uuid import uuid4

import status
from flask import Blueprint, abort, request
from flask.views import MethodView
from sqlalchemy import false, update
from sqlalchemy.orm.exc import NoResultFound

from src.exceptions import (
    RecipientNotExistError, SenderNotEnoughMoneyError, SenderNotExistError,
)
from src.extensions import db

from .models import CustomerModel, WalletModel, register_operation
from .schemas import (
    CustomerSchema, ReplenishmentSchema, TransferSchema, validate,
)


blueprint_v1 = Blueprint('v1', __name__, url_prefix='/v1')


class CustomerIndex(MethodView):
    def get(self, customer_id: int):
        # pylint: disable=no-self-use,no-member
        try:
            customer = CustomerModel\
                .query\
                .filter_by(id=customer_id, deleted=False)\
                .one()
        except NoResultFound:
            abort(status.HTTP_404_NOT_FOUND)
        return {'id': customer.id, 'name': customer.name}

    @validate(CustomerSchema)
    def put(self, customer_id: int):
        # pylint: disable=no-self-use,no-member
        try:
            count = CustomerModel\
                .query\
                .filter_by(id=customer_id, deleted=False)\
                .update({'name': request.valid_json['name']})
        except Exception:
            db.session.rollback()
            raise
        else:
            if count == 0:
                abort(status.HTTP_404_NOT_FOUND)
            db.session.commit()
            return {'id': customer_id, 'name': request.valid_json['name']}

    def delete(self, customer_id: int):
        # pylint: disable=no-self-use,no-member
        try:
            row_id = CustomerModel\
                .query\
                .filter_by(id=customer_id, deleted=False)\
                .update({'deleted': True})
        except Exception:
            db.session.rollback()
            raise
        else:
            if row_id == 0:
                abort(status.HTTP_404_NOT_FOUND)
            db.session.commit()
            return dict(), status.HTTP_204_NO_CONTENT

    @validate(CustomerSchema)
    def post(self):
        # pylint: disable=no-self-use,no-member
        try:
            customer = CustomerModel(name=request.valid_json['name'])
            db.session.add(customer)
        except Exception:
            db.session.rollback()
            raise
        else:
            db.session.commit()
            return {'id': customer.id}, status.HTTP_201_CREATED


customer_index_view = CustomerIndex.as_view('customer_api')
blueprint_v1.add_url_rule(
    '/customer/<int:customer_id>',
    view_func=customer_index_view,
    methods=['GET', 'PUT', 'DELETE'],
)
blueprint_v1.add_url_rule(
    '/customer',
    view_func=customer_index_view,
    methods=['POST'],
)


@blueprint_v1.route(
    '/customer/<int:customer_id>/replenishment', methods=['POST'],
)
@validate(ReplenishmentSchema)
def replenishment(customer_id: int):
    # pylint: disable=no-member
    amount = request.valid_json['amount']
    try:
        query = update(WalletModel)\
            .values(amount=WalletModel.amount + amount)\
            .where(CustomerModel.id == WalletModel.customer_id)\
            .where(CustomerModel.deleted == false())\
            .where(CustomerModel.id == customer_id)\
            .returning(WalletModel.id, WalletModel.amount)
        wallet = db.session.execute(query).fetchone()
        if not wallet:
            raise SenderNotExistError('Sender not exist')
        amount_was = wallet.amount - amount
        transaction = \
            register_operation(wallet.id, amount_was, wallet.amount, amount)
    except SenderNotExistError:
        db.session.rollback()
        abort(status.HTTP_404_NOT_FOUND)
    except Exception:
        db.session.rollback()
        raise
    else:
        db.session.commit()
        return {
            'transaction': transaction,
            'customer_id': customer_id,
            'amount_was': amount_was,
            'amount_become': wallet.amount,
            'operation_amount': amount,
        }


@blueprint_v1.route(
    '/customer/<int:sender_id>/transfer', methods=['POST'],
)
@validate(TransferSchema)
def transfer(sender_id: int):
    # pylint: disable=no-member
    recipient_id = request.valid_json['customer_id']
    amount = request.valid_json['amount']
    try:
        wallets = WalletModel\
            .query\
            .filter(CustomerModel.deleted == false())\
            .filter(CustomerModel.id.in_((sender_id, recipient_id)))\
            .with_for_update()\

        sender_wallet = recipient_wallet = None
        for wallet in wallets:
            if wallet.id == sender_id:
                sender_wallet = wallet
            elif wallet.id == recipient_id:
                recipient_wallet = wallet

        if not sender_wallet:
            raise SenderNotExistError('Sender not exist')
        if not recipient_wallet:
            raise RecipientNotExistError(
                f"Customer {recipient_id} doesn't exist",
            )

        sender_amount_was = sender_wallet.amount
        recipient_amount_was = recipient_wallet.amount
        sender_wallet.amount -= amount
        recipient_wallet.amount += amount

        if sender_wallet.amount < 0:
            raise SenderNotEnoughMoneyError(
                f"Customer {sender_id} doesn't have enough money",
            )
        transaction = uuid4()
        register_operation(
            sender_wallet.id,
            sender_wallet.amount + amount,
            sender_wallet.amount,
            -amount,
            transaction,
        )
        register_operation(
            recipient_wallet.id,
            recipient_wallet.amount - amount,
            recipient_wallet.amount,
            amount,
            transaction,
        )
    except SenderNotExistError:
        abort(status.HTTP_404_NOT_FOUND)
    except Exception:
        db.session.rollback()
        raise
    else:
        db.session.commit()
        return {
            'transaction': transaction,
            'sender': {
                'customer_id': sender_id,
                'amount_was': sender_amount_was,
                'amount_become': sender_wallet.amount,
                'operation_amount': - amount,
            },
            'recipient': {
                'customer_id': recipient_id,
                'amount_was': recipient_amount_was,
                'amount_become': recipient_wallet.amount,
                'operation_amount': amount,
            }
        }
