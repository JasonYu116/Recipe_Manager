import requests
import time

def run_mealdb_import():
    search_term = 'breakfast'
    imported_count = 0
    from .common import db

    print(f"Fetching category: {search_term}")
    resp = requests.get(f'https://www.themealdb.com/api/json/v1/1/filter.php?c={search_term}')
    try:
        data = resp.json()
    except Exception as e:
        print(f"Failed to parse list for {search_term}: {e}")
        return

    meals = data.get('meals', [])
    if not meals:
        print("No meals found in category.")
        return

    for meal_summary in meals:
        meal_id = meal_summary.get('idMeal')
        meal_detail_resp = requests.get(f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}')
        try:
            meal_detail_data = meal_detail_resp.json()
        except Exception as e:
            print(f"Failed to parse meal {meal_id}: {e}")
            continue

        if not meal_detail_data.get('meals'):
            continue

        meal_detail = meal_detail_data['meals'][0]
        recipe_name = meal_detail.get('strMeal')
        if db(db.recipe.name == recipe_name).count() > 0:
            print(f"Skipping duplicate recipe: {recipe_name}")
            continue 

        recipe_id = db.recipe.insert(
            name=recipe_name,
            type=meal_detail.get('strCategory', 'General'),
            # not sure what to put in the desc so it's blank for now
            description=meal_detail.get('', ''),
            image=meal_detail.get('strMealThumb', ''),
            instruction_steps=meal_detail.get('strInstructions', ''),
            servings=1,
            author=None
        )

        for i in range(1, 21):
            ing_name = meal_detail.get(f'strIngredient{i}')
            measure = meal_detail.get(f'strMeasure{i}')

            if ing_name and ing_name.strip():
                ing = db(db.ingredient.name == ing_name.strip()).select().first()
                if not ing:
                    ing_id = db.ingredient.insert(
                        name=ing_name.strip(),
                        unit='unit',
                        calories_per_unit=0,
                        description=''
                    )
                else:
                    ing_id = ing.id

                db.recipe_ingredient.insert(
                    recipe_id=recipe_id,
                    ingredient_id=ing_id,
                    quantity_per_serving=measure.strip() if measure else '1'
                )

        db.commit()
        time.sleep(0.1)  
        imported_count += 1
        print(f"Imported recipe: {recipe_name}")

    print(f"Import complete! Total recipes added: {imported_count}")