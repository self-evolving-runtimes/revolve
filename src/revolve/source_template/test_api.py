import json
import logging
import os

import pytest
from falcon import testing

from api import app
from utils import get_unique_id

@pytest.fixture
def client():
    return testing.TestClient(app)

def test_hello_db(client):
    response = client.simulate_get("/hello_db")
    print(response.content)  # Printing response is obligatory for debugging
    assert response.status == "200 OK"
    assert "message" in json.loads(response.content)
    assert "data" in json.loads(response.content)
