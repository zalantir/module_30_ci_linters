from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    views: Mapped[int] = mapped_column(default=0)
    cook_time: Mapped[int]
    description: Mapped[str]

    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Recipe {self.name!r} ({self.cook_time} min)>"


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")

    __table_args__ = (UniqueConstraint("recipe_id", "name"),)

    def __repr__(self) -> str:
        return f"<Ingredient {self.name!r}>"
