from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc, desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .dependencies import get_session
from .models import Ingredient, Recipe
from .schemas import RecipeCreate, RecipeCreated, RecipeDetail, RecipeListItem

api = APIRouter(prefix="/api", tags=["api"])


@api.get(
    "/recipes",
    response_model=list[RecipeListItem],
    summary="Получить список рецептов",
)
async def api_list_recipes(
    session: AsyncSession = Depends(get_session),
) -> list[RecipeListItem]:
    statement = select(Recipe.id, Recipe.name, Recipe.views, Recipe.cook_time).order_by(
        desc(Recipe.views), asc(Recipe.cook_time), asc(Recipe.id)
    )
    rows = (await session.execute(statement)).all()
    return [
        RecipeListItem(
            id=row.id, name=row.name, views=row.views, cook_time=row.cook_time
        )
        for row in rows
    ]


@api.get(
    "/recipes/{recipe_id}",
    response_model=RecipeDetail,
    summary="Получить рецепт по ID",
    responses={404: {"description": "Рецепт не найден"}},
)
async def api_get_recipe(
    recipe_id: int, session: AsyncSession = Depends(get_session)
) -> RecipeDetail:
    await session.execute(
        update(Recipe).where(Recipe.id == recipe_id).values(views=Recipe.views + 1)
    )
    await session.commit()

    statement = (
        select(Recipe)
        .options(selectinload(Recipe.ingredients))
        .where(Recipe.id == recipe_id)
    )
    recipe = (await session.execute(statement)).scalars().first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    return RecipeDetail(
        id=recipe.id,
        name=recipe.name,
        views=recipe.views,
        cook_time=recipe.cook_time,
        description=recipe.description,
        ingredients=[ingredient.name for ingredient in recipe.ingredients],
    )


@api.post(
    "/recipes",
    response_model=RecipeCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Создать рецепт",
    responses={
        201: {"description": "Создано"},
        409: {"description": "Конфликт уникальности"},
    },
)
async def api_create_recipe(
    payload: RecipeCreate, session: AsyncSession = Depends(get_session)
) -> RecipeCreated:
    seen = set()
    names: list[str] = []
    for name in payload.ingredients:
        name = name.strip()
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            names.append(name)

    recipe = Recipe(
        name=payload.name.strip(),
        cook_time=payload.cook_time,
        description=payload.description.strip(),
    )
    recipe.ingredients = [Ingredient(name=name) for name in names]

    session.add(recipe)
    try:
        await session.commit()
    except IntegrityError as err:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="Рецепт с таким названием уже существует"
        ) from err

    return RecipeCreated(id=recipe.id)
