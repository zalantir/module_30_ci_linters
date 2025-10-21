from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import asc, desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import RedirectResponse

from .dependencies import get_session
from .models import Ingredient, Recipe
from .schemas import recipe_form_openapi

router = APIRouter(tags=["html"])
_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=_TEMPLATES_DIR)


@router.get(
    "/recipes/new",
    name="new_recipe",
    summary="Форма создания рецепта",
    response_class=HTMLResponse,
)
async def new_recipe(request: Request) -> Any:
    return templates.TemplateResponse(
        request,
        "recipe_form.html",
        {
            "values": {
                "name": "",
                "cook_time": "",
                "description": "",
                "ingredients": "",
            },
            "error": None,
        },
    )


@router.get(
    "/recipes",
    summary="HTML-страница с таблицей рецептов",
    response_class=HTMLResponse,
)
async def recipes_page(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Any:
    """Возвращает HTML-страницу с таблицей рецептов"""
    statement = select(Recipe).order_by(
        desc(Recipe.views), asc(Recipe.cook_time), asc(Recipe.id)
    )
    result = await session.execute(statement)
    recipes = result.scalars().all()
    rows = [[row.name, row.views, row.cook_time] for row in recipes]
    links = [request.url_for("recipe_detail", recipe_id=row.id) for row in recipes]

    return templates.TemplateResponse(
        request, "recipes.html", {"rows": rows, "links": links}
    )


@router.get(
    "/recipes/{recipe_id}",
    summary="Получить рецепт по ID",
    response_class=HTMLResponse,
)
async def recipe_detail(
    recipe_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Any:
    await session.execute(
        update(Recipe).where(Recipe.id == recipe_id).values(views=Recipe.views + 1)
    )
    await session.commit()

    statement = (
        select(Recipe)
        .options(selectinload(Recipe.ingredients))
        .where(Recipe.id == recipe_id)
    )
    result = await session.execute(statement)
    recipes = result.scalars().all()
    rows = [
        [
            row.name,
            row.views,
            row.cook_time,
            row.description,
            ", ".join(ingredient.name for ingredient in row.ingredients),
        ]
        for row in recipes
    ]

    return templates.TemplateResponse(request, "recipe_detail.html", {"rows": rows})


@router.post(
    "/recipes",
    name="create_recipe",
    summary="Создать рецепт",
    response_class=HTMLResponse,
    openapi_extra=recipe_form_openapi(),
)
async def create_recipe(
    request: Request,
    session: AsyncSession = Depends(get_session),
    name: str = Form(...),
    cook_time: int = Form(...),
    description: str = Form(...),
    ingredients: str = Form(...),
) -> Any:
    recipe_name = name.strip()
    description = description.strip()
    raw_ingredients = ingredients.strip()

    if not name or cook_time <= 0 or not raw_ingredients:
        return templates.TemplateResponse(
            request,
            "recipe_form.html",
            {
                "values": {
                    "name": name,
                    "cook_time": cook_time if cook_time else "",
                    "description": description,
                    "ingredients": raw_ingredients,
                },
                "error": "Заполните все поля корректно (время готовки > 0, список ингредиентов не пустой).",  # noqa: E501
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    parts = [
        part.strip()
        for chunk in raw_ingredients.splitlines()
        for part in chunk.split(",")
    ]
    names = [part for part in parts if part]
    seen = set()
    ingredients_names = []
    for name in names:
        if name.lower() not in seen:
            seen.add(name.lower())
            ingredients_names.append(name)

    recipe = Recipe(
        name=recipe_name,
        cook_time=cook_time,
        description=description,
        views=0,
    )
    recipe.ingredients = [
        Ingredient(name=ingredient) for ingredient in ingredients_names
    ]

    session.add(recipe)

    try:
        await session.commit()
    except IntegrityError as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse(
            request,
            "recipe_form.html",
            {
                "values": {
                    "name": name,
                    "cook_time": cook_time,
                    "description": description,
                    "ingredients": raw_ingredients,
                },
                "error": "Рецепт с таким названием уже существует.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    detail_url = request.url_for("recipe_detail", recipe_id=recipe.id)
    return RedirectResponse(url=detail_url, status_code=status.HTTP_303_SEE_OTHER)
