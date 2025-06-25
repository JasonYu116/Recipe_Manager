from py4web import action, request, response, URL, HTTP
from py4web.utils.form import Form, FormStyleBulma
from .models import auth, db
from .common import session
import os
from . import settings
import json
import re
from py4web.utils.url_signer import URLSigner
import uuid
from datetime import datetime
import time

# --------------------- PAGES --------------------------
@action("index")
@action("/")
@action.uses("index.html", db)
def index():
    user = auth.get_user()
    return dict(user=user)

url_signer = URLSigner(session)

@action("ingredients")
@action.uses("ingredients.html", db)
def ingredients():
    return dict(api_base=URL("api/ingredients"))

@action("recipe_page")
@action.uses("recipe.html", db)
def recipe_page():
    user = auth.get_user()
    return dict(
        api_base=URL("api/recipes"),
        user_id=user["id"] if user else None,
        user=user 
    )

@action("post")
@action.uses("post.html", db, auth.user)
def post():
    return dict(auth=auth, timestamp=int(time.time()))

# ------- INGREDIENTS -------
@action("api/ingredients", method=["GET"])
@action.uses(db)
def get_ingredients():
    search = request.params.get("search", "").lower()
    rows = db(db.ingredient.name.ilike(f"%{search}%")).select(orderby=db.ingredient.name)
    return dict(ingredients=rows.as_list())

@action("api/ingredients", method=["POST"])
@action.uses(db, auth.user)
def add_ingredient():
    data = request.json
    name = data.get("name", "").strip()
    unit = data.get("unit", "").strip()
    calories_per_unit = data.get("calories_per_unit")
    description = data.get("description", "").strip()
    
    # Validation
    if not name or calories_per_unit is None:
        return dict(success=False, error="Missing required fields.")
    

    if db(db.ingredient.name == name).select().first():
        return dict(success=False, error="Ingredient already exists.")
    
    db.ingredient.insert(
        name=name,
        unit=unit,
        calories_per_unit=calories_per_unit,
        description=description
    )
    return dict(success=True)

@action("api/ingredients/<ingredient_id:int>", method=["DELETE"])
@action.uses(db, auth.user)
def delete_ingredient(ingredient_id):
    if db(db.recipe_ingredient.ingredient_id == ingredient_id).count() > 0:
        return dict(success=False, error="Ingredient is in use and cannot be deleted.")
    
    db(db.ingredient.id == ingredient_id).delete()
    return dict(success=True)

# --------------------- RECIPE API --------------------------

# API: Get all recipes
@action("api/recipes", method="GET")
@action.uses(db)
def get_recipes():
    search = request.params.get("search", "")
    query = db.recipe

    if search:
        search_pattern = f"%{search}%"
        query = (db.recipe.name.ilike(search_pattern)) | \
                (db.recipe.description.ilike(search_pattern)) | \
                (db.recipe.type.ilike(search_pattern))

    ingredient_id = request.params.get("ingredient_id")
    if ingredient_id:
        recipe_ids = db(db.recipe_ingredient.ingredient_id == ingredient_id).select(db.recipe_ingredient.recipe_id)
        recipe_ids = [r.recipe_id for r in recipe_ids]
        query &= db.recipe.id.belongs(recipe_ids)

    recipes = []
    for r in db(query).select(orderby=db.recipe.name):
        ingredients = db((db.recipe_ingredient.recipe_id == r.id) &
                         (db.recipe_ingredient.ingredient_id == db.ingredient.id))\
                         .select(db.recipe_ingredient.ALL, db.ingredient.ALL)

        recipe_ingredients = [{
            "ingredient_id": i.ingredient.id,
            "name": i.ingredient.name,
            "unit": i.ingredient.unit,
            "calories_per_unit": i.ingredient.calories_per_unit,
            "quantity_per_serving": i.recipe_ingredient.quantity_per_serving,
        } for i in ingredients]

        user_rating = None
        # avg
        avg_rating_row = db(db.rating.recipe_id == r.id).select(db.rating.rating).as_list()
        if avg_rating_row:
            avg_rating = round(sum(x["rating"] for x in avg_rating_row) / len(avg_rating_row), 1)
        else:
            avg_rating = 5.0  # default 5 
        rating_count = len(avg_rating_row)    

        if auth.current_user:
            user_id = auth.current_user.get("id")
            rating_row = db((db.rating.recipe_id == r.id) & (db.rating.user_id == user_id)).select().first()
            if rating_row:
                user_rating = rating_row.rating

        recipes.append(dict(
            r.as_dict(),
            ingredients=recipe_ingredients,
            user_rating=user_rating,
            avg_rating=avg_rating,
            rating_count=rating_count
        ))




    return dict(recipes=recipes)

# API: Create new recipe
@action("api/recipes", method="POST")
@action.uses(db, auth.user)
def create_recipe():
    data = request.json or {}

    # Validate required fields
    errors = {}
    if not data.get("name"):
        errors["name"] = "Name required"

    if errors:
        return dict(errors=errors, id=None)

    # Insert recipe
    recipe_id = db.recipe.insert(
        name=data["name"],
        type=data.get("type", ""),
        description=data.get("description", ""),
        #in the uplaods folder
        image=data.get("image", ""),  
        instruction_steps=data.get("instruction_steps", ""),
        servings=data.get("servings", 1),
        author=auth.current_user.get("id")
    )

    # ingridients qty
    for ing in data.get("ingredient_quantities", []):
        db.recipe_ingredient.insert(
            recipe_id=recipe_id,
            ingredient_id=ing["ingredient_id"],
            quantity_per_serving=ing["quantity_per_serving"]
        )

    db.commit()
    return dict(id=recipe_id, errors={})

# API: Update recipe (
@action("api/recipes/<recipe_id:int>", method="PUT")
@action.uses(db, auth.user)
def update_recipe(recipe_id):
    recipe = db.recipe[recipe_id]
    if not recipe:
        response.status = 404
        return dict(success=False, error="Recipe not found")

    if recipe.author != auth.current_user.get("id"):
        response.status = 403
        return dict(success=False, error="You can only edit your own recipes")

    data = request.json
    
    # Validate required fields
    if not data.get('name') or not data.get('type') or not data.get('description') or not data.get('instruction_steps'):
        return dict(success=False, error="All fields are required")
    
    if not isinstance(data.get('servings'), int) or data.get('servings') < 1:
        return dict(success=False, error="Servings must be a positive integer")
    
    try:
        # Update the recipe
        db(db.recipe.id == recipe_id).update(
            name=data['name'],
            type=data['type'],
            description=data['description'],
            servings=data['servings'],
            instruction_steps=data['instruction_steps']
        )
        db.commit()
        
        return dict(success=True, message="Recipe updated successfully")
    
    except Exception as e:
        db.rollback()
        return dict(success=False, error=str(e))

# API: Delete recipe
@action("api/recipes/<recipe_id:int>", method="DELETE")
@action.uses(db, auth.user)
def delete_recipe(recipe_id):
    recipe = db.recipe[recipe_id]
    if not recipe or recipe.author != auth.current_user.get("id"):
        response.status = 403
        return dict(error="Unauthorized")
    
    # Delete associated recipe-ingredient 
    db(db.recipe_ingredient.recipe_id == recipe_id).delete()
    # Then delete the recipe
    db(db.recipe.id == recipe_id).delete()
    db.commit()
    return dict(success=True)


@action('upload', method=['POST', 'OPTIONS'])
@action.uses(db, auth.user)  
def upload():
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return ''
    
    upload_file = request.files.get('image')
    if not upload_file:
        return dict(success=False, error='No file uploaded')

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_extension = upload_file.filename.lower().split('.')[-1]
    if file_extension not in allowed_extensions:
        return dict(success=False, error='Invalid file type. Only images are allowed.')

    # Generate unique filename to prevent conflicts
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    

    if not os.path.exists(settings.UPLOAD_FOLDER):
        os.makedirs(settings.UPLOAD_FOLDER)
    
    # Save file
    file_path = os.path.join(settings.UPLOAD_FOLDER, unique_filename)
    upload_file.save(file_path)

    # Return just the filename 
    return dict(
        success=True,
        filename=unique_filename
    )


#get it from the uploads folder
@action("uploads/<filename>")
@action.uses(db)
def serve_upload(filename):
    """Serve uploaded files from the uploads folder"""
    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.UPLOAD_FOLDER)):
        raise HTTP(403, "Access denied")
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTP(404, "File not found")
    
    # Determine content type
    content_type = "application/octet-stream"
    if filename.lower().endswith('.png'):
        content_type = "image/png"
    elif filename.lower().endswith(('.jpg', '.jpeg')):
        content_type = "image/jpeg"
    elif filename.lower().endswith('.gif'):
        content_type = "image/gif"
    elif filename.lower().endswith('.webp'):
        content_type = "image/webp"
    
    # Set the content type header
    response.headers['Content-Type'] = content_type
    
    # Read and return the file content
    with open(file_path, 'rb') as f:
        return f.read()



@action('api/recipes/like/<recipe_id:int>', method='POST')
@action.uses(db, auth.user)
def like_recipe(recipe_id):
    try:
        recipe = db.recipe[recipe_id]
        if not recipe:
            return dict(success=False, error="Recipe not found")
        
        # Initialize likes to 0 if None
        current_likes = recipe.likes if recipe.likes is not None else 0
        new_likes = current_likes + 1
        
        # Update the recipe
        recipe.update_record(likes=new_likes)
        db.commit()
        
        return dict(success=True, likes=new_likes)
    except Exception as e:
        db.rollback()
        return dict(success=False, error=str(e))

@action('api/recipes/dislike/<recipe_id:int>', method='POST')
@action.uses(db, auth.user)
def dislike_recipe(recipe_id):
    try:
        recipe = db.recipe[recipe_id]
        if not recipe:
            return dict(success=False, error="Recipe not found")
        
        # Initialize dislikes to 0 if None
        current_dislikes = recipe.dislikes if recipe.dislikes is not None else 0
        new_dislikes = current_dislikes + 1
        
        # Update the recipe
        recipe.update_record(dislikes=new_dislikes)
        db.commit()
        
        return dict(success=True, dislikes=new_dislikes)
    except Exception as e:
        db.rollback()
        return dict(success=False, error=str(e))

# jump to instruction details
@action("recipe/<recipe_id:int>/instructions")
@action.uses("instruction.html", db)
def recipe_instructions(recipe_id):
    r = db.recipe[recipe_id]
    if not r:
        raise HTTP(404)

    # Get ingredient linked to the recipe
    rows = db((db.recipe_ingredient.recipe_id == r.id) &
              (db.recipe_ingredient.ingredient_id == db.ingredient.id))\
              .select(db.recipe_ingredient.ALL, db.ingredient.ALL)

    ingredients = [{
        "name": row.ingredient.name,
        "unit": row.ingredient.unit,
        "quantity_per_serving": row.recipe_ingredient.quantity_per_serving,
    } for row in rows]

    return dict(recipe=r, ingredients=ingredients)

@action("api/rate_recipe", method=["POST"])
@action.uses(db, auth.user)
def rate_recipe():
    data = request.json
    recipe_id = data.get("recipe_id")
    rating = data.get("rating")
    user_id = auth.current_user.get("id")

    if not recipe_id or not rating or not (1 <= rating <= 5):
        return dict(success=False, error="Invalid input")

    existing = db((db.rating.recipe_id == recipe_id) & (db.rating.user_id == user_id)).select().first()
    if existing:
        existing.update_record(rating=rating, timestamp=datetime.utcnow())
    else:
        db.rating.insert(recipe_id=recipe_id, user_id=user_id, rating=rating)

    return dict(success=True)


@action("recipe/<recipe_id:int>/reviews")
@action.uses("reviews.html", db, auth.user)
def recipe_reviews(recipe_id):
    recipe = db.recipe[recipe_id]
    if not recipe:
        raise HTTP(404)

    reviews = db(db.review.recipe_id == recipe_id).select(
    db.review.ALL,
    db.auth_user.first_name,
    left=db.auth_user.on(db.review.user_id == db.auth_user.id),
    orderby=~db.review.timestamp
)
    return dict(recipe=recipe, reviews=reviews)

@action("api/review", method=["POST"])
@action.uses(db, auth.user)
def post_review():
    data = request.json
    recipe_id = data.get("recipe_id")
    content = data.get("content", "").strip()
    if not recipe_id or not content:
        return dict(success=False, error="Missing fields")

    db.review.insert(recipe_id=recipe_id, user_id=auth.current_user["id"], content=content)
    return dict(success=True)
