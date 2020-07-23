# -*- coding: utf-8 -*-
import json

import pytest
import status

from src.api.models import CustomerModel
from src.extensions import db


@pytest.mark.user
def test_not_valid_json_data_for_customer_creation(client):
    response = client.post('/v1/customer')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json.loads(response.data) == {
        'message':
            [
                {
                    'loc': ['name'],
                    'msg': 'field required',
                    'type': 'value_error.missing'
                }
            ],
        'status': 'error',
    }


@pytest.mark.user
def test_customer_reception_non_existing(client, current_app):
    # pylint: disable=unused-argument
    with current_app.app_context():
        response = client.get('/v1/customer/1')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.user
def test_customer_reception(client, current_app):
    # pylint: disable=unused-argument,no-member
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
        response = client.get('/v1/customer/1')
        assert response.status_code == status.HTTP_200_OK
        assert json.loads(response.data) == {'id': 1, 'name': 'Иванов'}


@pytest.mark.user
def test_customer_creation(client, current_app):
    # pylint: disable=unused-argument
    response = client.post('/v1/customer', json={'name': 'Иванов'})
    assert response.status_code == status.HTTP_201_CREATED
    assert json.loads(response.data) == {'id': 1}

    with current_app.app_context():
        customer = CustomerModel.query.get(1)
    assert customer.name == 'Иванов'
    assert customer.deleted is False


@pytest.mark.user
def test_customer_update(client, current_app):
    # pylint: disable=unused-argument,no-member
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
        response = client.put('/v1/customer/1', json={'name': 'Сидоров'})
        assert response.status_code == status.HTTP_200_OK
        assert json.loads(response.data) == {'id': 1, 'name': 'Сидоров'}


@pytest.mark.user
def test_customer_delete(client, current_app):
    # pylint: disable=unused-argument,no-member
    with current_app.app_context():
        customer = CustomerModel(name='Иванов')
        db.session.add(customer)
        db.session.commit()
        response = client.delete('/v1/customer/1')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        customer = CustomerModel.query.get(1)
        assert customer.deleted is True


@pytest.mark.user
def test_customer_delete_no_existing(client, current_app):
    # pylint: disable=unused-argument,no-member
    with current_app.app_context():
        response = client.delete('/v1/customer/2')
        assert response.status_code == status.HTTP_404_NOT_FOUND
