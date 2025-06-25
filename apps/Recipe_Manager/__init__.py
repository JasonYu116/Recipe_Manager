# check compatibility
import py4web

assert py4web.check_compatible("1.20190709.1")

# by importing controllers you expose the actions defined in it
from . import controllers

# by importing db you expose it to the _dashboard/dbadmin
from .models import db

# import the scheduler
from .tasks import scheduler

# optional parameters
__version__ = "0.0.0"
__author__ = "you <you@example.com>"
__license__ = "anything you want"

# import mealdb
try:
    from .mealdb_import import run_mealdb_import

    if db(db.recipe).count() == 0:
        run_mealdb_import()
except Exception as e:  # pragma: no cover - best effort import
    print("MealDB import failed:", e)