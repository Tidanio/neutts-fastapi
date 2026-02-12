from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client without loading real models."""
    from api.src.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
