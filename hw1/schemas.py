from typing import List

from pydantic import BaseModel, ConfigDict, Field


class RecipeListItem(BaseModel):
    id: int = Field(..., description="ID рецепта")
    name: str = Field(..., description="Название блюда", examples=["Шакшука"])
    views: int = Field(..., ge=0, description="Количество просмотров")
    cook_time: int = Field(..., ge=1, description="Время готовки в минутах")
    model_config = ConfigDict(from_attributes=True)


class RecipeDetail(BaseModel):
    id: int
    name: str
    views: int
    cook_time: int
    description: str
    ingredients: List[str]
    model_config = ConfigDict(from_attributes=True)


class RecipeCreate(BaseModel):
    name: str = Field(..., description="Название")
    cook_time: int = Field(..., description="Время готовки в минутах")
    description: str = Field(..., description="Описание рецепта")
    ingredients: List[str] = Field(..., description="Список ингредиентов")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Картофельное пюре с чесноком",
                "cook_time": 30,
                "description": "Нежное пюре со сливочным маслом и чесноком.",
                "ingredients": [
                    "Картофель",
                    "Молоко",
                    "Масло сливочное",
                    "Соль",
                    "Чеснок",
                ],
            }
        }
    }


class RecipeCreated(BaseModel):
    id: int = Field(..., description="ID созданного рецепта")


def recipe_form_openapi() -> dict:
    """Схема requestBody для html формы,
    чтобы в Swagger стояли нужные default-значения."""
    return {
        "requestBody": {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "required": ["name", "cook_time", "description", "ingredients"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "title": "Название",
                                "default": "Картофельное пюре с чесноком",
                            },
                            "cook_time": {
                                "type": "integer",
                                "title": "Время готовки (мин)",
                                "default": 30,
                            },
                            "description": {
                                "type": "string",
                                "title": "Описание",
                                "default": "Нежное пюре со сливочным маслом и чесноком.",  # noqa: E501
                            },
                            "ingredients": {
                                "type": "string",
                                "title": "Ингредиенты",
                                "default": "Картофель, Молоко, Масло сливочное, Соль, Чеснок",  # noqa: E501
                            },
                        },
                    }
                }
            },
        }
    }
