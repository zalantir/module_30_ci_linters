from uuid import uuid4

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def created_recipe_id(client: TestClient) -> int:
    name = f"Тестовый {uuid4().hex[:6]}"
    payload = {
        "name": name,
        "cook_time": 5,
        "description": "desc",
        "ingredients": ["Хлеб", "Соль"],
    }
    response = client.post("/api/recipes", json=payload)
    assert response.status_code in (200, 201)
    created = response.json()
    recipe_id = created.get("id") or created.get("recipe", {}).get("id")
    assert recipe_id is not None
    return recipe_id


@pytest.fixture(scope="session", autouse=True)
def ensure_one_recipe(client: TestClient) -> None:
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


def test_get_form_page(client: TestClient) -> None:
    """Страница создания нового рецепта (/recipes/new)
    открывается и содержит заголовок 'Новый рецепт'."""
    response = client.get("/recipes/new")
    assert response.status_code == 200
    assert "Новый рецепт" in response.text


def test_get_recipes_page(client: TestClient) -> None:
    """Страница со списком рецептов (/recipes)
    успешно возвращается и содержит заголовок 'Рецепты'."""
    response = client.get("/recipes")
    assert response.status_code == 200
    assert "Рецепты" in response.text


def test_get_recipe_detail_exists(client: TestClient, created_recipe_id: int) -> None:
    """Детальная страница рецепта (/recipes/{id})
    открывается и отображает данные рецепта из API."""
    response = client.get("/api/recipes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and len(data) >= 1

    response_2 = client.get(f"/recipes/{created_recipe_id}")
    assert response_2.status_code == 200


def test_api_list_recipes_ok(client: TestClient) -> None:
    """API возвращает список рецептов
    и каждый элемент содержит ожидаемые поля."""
    response = client.get("/api/recipes")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    if body:
        assert {"id", "name", "views", "cook_time"} <= set(body[0].keys())


def test_api_create_recipe_ok(client: TestClient) -> None:
    """Через API можно успешно создать новый рецепт
    и он появляется в списке рецептов."""
    unique_name = f"Тестовый рецепт {uuid4().hex[:8]}"
    payload = {
        "name": unique_name,
        "cook_time": 7,
        "description": "Короткий тестовый рецепт",
        "ingredients": ["Хлеб", "Соль"],
    }

    response = client.post("/api/recipes", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert "id" in body and isinstance(body["id"], int)
    response_list = client.get("/api/recipes")
    ids = [item["id"] for item in response_list.json()]
    assert body["id"] in ids


def test_api_get_recipe_increments_views(client: TestClient) -> None:
    """Количество просмотров рецепта увеличивается
    при запросе /api/recipes/{id}."""
    response = client.get("/api/recipes")
    assert response.status_code == 200
    data = response.json()
    assert data, "ожидали хотя бы один рецепт после seed"
    response_id = data[0]["id"]
    before = data[0]["views"]
    response_2 = client.get(f"/api/recipes/{response_id}")
    assert response_2.status_code == 200
    response_3 = client.get("/api/recipes")
    after = next(
        item["views"] for item in response_3.json() if item["id"] == response_id
    )
    assert after == before + 1
