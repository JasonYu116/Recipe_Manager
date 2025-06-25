# Recipe_Manager
CSE183 Project Team 17:
- yzhan983@ucsc.edu
- helamni@ucsc.edu
- jaleyu@ucsc.edu
- tchang52@ucsc.edu
- szhu49@ucsc.edu
- jlee897@ucsc.edu

## About
Custom Recipe Manager
A web-based recipe manager built with Py4web. The Users can sign up, manage ingredients, create, update and delete recipes, and view nutrition information.
------
## Dependencies
1 Python  
2 y4web   
3 A browser  

## Installation/Setup  
1. Clone the repository  
   git clone git@github.com:ucsc2025-cse183/project-17.git  
   cd project-17  
2. Start the Py4web server:  
py4web run apps/Recipe_Manager  
3. Open your browser and navigate to http://localhost:8000  

## Functionality
- User Authentication  
- Ingredient Management  
- Search Ingredients  
- Add New Ingredient  
- Navigate to recipe  
- Search Recipes  
- Add New Recipe  
- Calorie Calculations  

## Database Schema: 
- A table for ingredients with fields: name, unit, calories\_per\_unit, description  
- A table for recipes with fields: name, type, description, image, author, instruction\_steps, servings  
- A linking table to connect recipes and ingredients, with fields: recipe\_id, ingredient_id, quantity\_per\_serving  


