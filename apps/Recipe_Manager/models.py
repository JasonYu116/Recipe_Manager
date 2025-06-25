from datetime import datetime
from py4web import Field
from pydal.validators import IS_NOT_EMPTY, IS_FLOAT_IN_RANGE

from .common import db, auth

# Ingredients
db.define_table(
    'ingredient',
    Field('name', 'string'),
    Field('unit', 'string'),
    Field('calories_per_unit', 'float'),
    Field('description', 'text'),
)

db.ingredient.name.requires = IS_NOT_EMPTY()
db.ingredient.calories_per_unit.requires = IS_FLOAT_IN_RANGE(0, None)

# Recipes
db.define_table(
    'recipe',
    Field('name', 'string'),
    Field('type', 'string'),
    Field('description', 'text'),
    Field('image', 'string'),
    Field('author', 'reference auth_user'),
    Field('instruction_steps', 'text'),
    Field('servings', 'integer'),
    Field("likes", "integer", default=0),
    Field("dislikes", "integer", default=0),
)

# Linking table
db.define_table(
    'recipe_ingredient',
    Field('recipe_id', 'reference recipe'),
    Field('ingredient_id', 'reference ingredient'),
    Field('quantity_per_serving', 'string'),
)

db.commit()


db.define_table(
    "rating",
    Field("recipe_id", "reference recipe"),
    Field("user_id", "reference auth_user"),
    Field("rating", "integer"),  # 1 to 5
    Field("timestamp", "datetime", default=datetime.utcnow)
)

db.define_table(
    'review',
    Field('recipe_id', 'reference recipe'),
    Field('user_id', 'reference auth_user'),
    Field('content', 'text'),
    Field('timestamp', 'datetime', default=datetime.utcnow),
)

