from http import HTTPStatus

import pytest
from flask import current_app

from ...app import app


@pytest.fixture
def test_client():
    with app.app_context():
        current_app.testing = True
        client = current_app.test_client()
        return client


def test_health_check_live(test_client):
    response = test_client.get("/healthz/live")
    assert response.status_code == HTTPStatus.OK


def test_health_check_ready(test_client):
    response = test_client.get("/healthz/ready")
    assert response.status_code == HTTPStatus.OK
