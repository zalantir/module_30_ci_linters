from typing import Generator

import pytest
from fastapi.testclient import TestClient

from hw1.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def ensure_one_recipe(client: TestClient) -> None:
    """Гарантирует, что в БД есть хотя бы один рецепт перед запуском тестов."""
    resp = client.get("/api/recipes")
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, list) and len(data) > 0:
        return

    payload = {
        "name": "seed-recipe",
        "cook_time": 5,
        "description": "seed",
        "ingredients": ["Хлеб", "Соль"],
    }
    create = client.post("/api/recipes", json=payload)
    assert create.status_code in (200, 201), create.text
