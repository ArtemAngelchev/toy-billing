# -*- coding: utf-8 -*-
import json

import pytest
import status

from src.api.models import CustomerModel
from src.extensions import db


@pytest.mark.operation
def test_replenishment_invalid_amount(client, current_app):
    # pylint: disable=no-member
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
    response = \
        client.post('/v1/customer/1/replenishment', json={'amount': -200})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json.loads(response.data) == {
        'message':
            [
                {
                    'ctx': {
                        'limit_value': 1
                    },
                    'loc': ['amount'],
                    'msg': 'ensure this value is greater than or equal to 1',
                    'type': 'value_error.number.not_ge'
                }
            ],
        'status': 'error'
    }


@pytest.mark.operation
def test_replenishment_invalid_customer(client):
    # pylint: disable=no-member
    response = \
        client.post('/v1/customer/1/replenishment', json={'amount': 200})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json.loads(response.data) == {
        'message': 'Resource not found.',
        'status': 'error'
    }


@pytest.mark.operation
def test_replenishment(client, current_app):
    # pylint: disable=no-member
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
        response = \
            client.post('/v1/customer/1/replenishment', json={'amount': 200})
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.data)
        assert response_data['customer_id'] == 1
        assert response_data['amount_was'] == 0
        assert response_data['amount_become'] == 200
        assert response_data['operation_amount'] == 200
        customer = CustomerModel.query.get(1)
        operations = customer.wallet.operations
        assert len(operations) == 1
        assert operations[0].amount_was == 0
        assert operations[0].amount_become == 200
        assert operations[0].operation_amount == 200


@pytest.mark.operation
def test_replenishment_consistency(client, current_app, mocker):
    # pylint: disable=no-member
    mocker.patch(
        'src.api.views.register_operation', side_effect=RuntimeError('test'),
    )
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
        response = \
            client.post('/v1/customer/1/replenishment', json={'amount': 200})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        customer = CustomerModel.query.get(1)
        assert customer.wallet.amount == 0
        operations = customer.wallet.operations
        assert len(operations) == 0


@pytest.mark.operation
def test_transfer_not_enough_money(client, current_app):
    # pylint: disable=no-member
    with current_app.app_context():
        customer1 = CustomerModel(name='Иванов')
        customer2 = CustomerModel(name='Сидоров')
        db.session.add(customer1)
        db.session.add(customer2)
        db.session.commit()
        response = client.post(
            '/v1/customer/1/transfer',
            json={'customer_id': 2, 'amount': 100},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.data) == {
            'message': "Customer 1 doesn't have enough money",
            'status': 'error',
        }
        customer = CustomerModel.query.get(1)
        assert customer.wallet.amount == 0
        operations = customer.wallet.operations
        assert len(operations) == 0


@pytest.mark.operation
def test_transfer(client, current_app):
    # pylint: disable=no-member
    with current_app.app_context():
        customer1 = CustomerModel(name='Иванов')
        customer2 = CustomerModel(name='Сидоров')
        customer1.wallet.amount = 200
        db.session.add(customer1)
        db.session.add(customer2)
        db.session.commit()
        response = client.post(
            '/v1/customer/1/transfer',
            json={'customer_id': 2, 'amount': 100},
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.data)
        assert response_data['recipient'] == {
            'amount_become': 100,
            'amount_was': 0,
            'customer_id': 2,
            'operation_amount': 100,
        }
        assert response_data['sender'] == {
            'amount_become': 100,
            'amount_was': 200,
            'customer_id': 1,
            'operation_amount': -100,
        }
        customer1 = CustomerModel.query.get(1)
        assert customer1.wallet.amount == 100
        operations1 = customer1.wallet.operations
        assert len(operations1) == 1
        assert operations1[0].amount_was == 200
        assert operations1[0].amount_become == 100
        assert operations1[0].operation_amount == -100
        customer2 = CustomerModel.query.get(2)
        assert customer2.wallet.amount == 100
        operations2 = customer2.wallet.operations
        assert len(operations2) == 1
        assert operations2[0].amount_was == 0
        assert operations2[0].amount_become == 100
        assert operations2[0].operation_amount == 100


@pytest.mark.operation
def test_transfer_no_sender(client, current_app):
    # pylint: disable=no-member
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
        response = client.post(
            '/v1/customer/2/transfer',
            json={'customer_id': 1, 'amount': 100},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.operation
def test_transfer_no_recipient(client, current_app):
    # pylint: disable=no-member
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
        response = client.post(
            '/v1/customer/1/transfer',
            json={'customer_id': 2, 'amount': 100},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.data) == {
            'message': "Customer 2 doesn't exist",
            'status': 'error',
        }


@pytest.mark.operation
def test_transfer_consistency(client, current_app, mocker):
    # pylint: disable=no-member
    mocker.patch(
        'src.api.views.register_operation', side_effect=RuntimeError('test'),
    )
    with current_app.app_context():
        customer1 = CustomerModel(name='Иванов')
        customer2 = CustomerModel(name='Сидоров')
        customer1.wallet.amount = 200
        db.session.add(customer1)
        db.session.add(customer2)
        db.session.commit()
        response = client.post(
            '/v1/customer/1/transfer',
            json={'customer_id': 2, 'amount': 100},
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        customer1 = CustomerModel.query.get(1)
        customer2 = CustomerModel.query.get(2)
        assert customer1.wallet.amount == 200
        assert customer2.wallet.amount == 0

        customer1 = CustomerModel.query.get(1)
        assert customer1.wallet.amount == 200
        operations1 = customer1.wallet.operations
        assert len(operations1) == 0
        customer2 = CustomerModel.query.get(2)
        assert customer2.wallet.amount == 0
        operations2 = customer2.wallet.operations
        assert len(operations2) == 0
