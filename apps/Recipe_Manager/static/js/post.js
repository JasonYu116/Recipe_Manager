new Vue({
  el: "#post-page",
  data: {
    // INGREDIENT
    newIngredient: { name: "", unit: "", calories_per_unit: null, description: "" },
    ingredientError: null,
    // RECIPE
    newRecipe: { name: "", type: "", description: "", instruction_steps: "", servings: 1, image: "" },
    allIngredients: [],
    selectedIngredients: [],
    recipeError: null,
    // NEW: For dropdown functionality
    selectedIngredientId: "",
    ingredientQuantity: null
  },
  methods: {
    // INGREDIENT
    addIngredient() {
      this.ingredientError = null;
      fetch(window.api_ingredients, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.newIngredient)
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          alert("Ingredient added!");
          this.newIngredient = { name: "", unit: "", calories_per_unit: null, description: "" };
          this.loadIngredients();
        } else {
          this.ingredientError = data.error || "Error adding ingredient.";
        }
      });
    },
    
    // RECIPE
    addRecipe() {
      this.recipeError = null;
      fetch(window.api_recipes, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...this.newRecipe,
          ingredient_quantities: this.selectedIngredients
        })
      })
      .then(res => res.json())
      .then(data => {
        if (data.id) {
          alert("Recipe added!");
          this.newRecipe = { name: "", type: "", description: "", instruction_steps: "", servings: 1, image: "" };
          this.selectedIngredients = [];
          this.selectedIngredientId = "";
          this.ingredientQuantity = null;
        } else {
          this.recipeError = Object.values(data.errors || {}).join(", ") || "Error adding recipe.";
        }
      });
    },

    // NEW: Add ingredient to recipe from dropdown
    addIngredientToRecipe() {
      if (!this.selectedIngredientId || !this.ingredientQuantity) return;
      
      // Check if ingredient is already added
      const existingIndex = this.selectedIngredients.findIndex(
        sel => sel.ingredient_id === this.selectedIngredientId
      );
      
      if (existingIndex >= 0) {
        // Update existing ingredient quantity
        this.selectedIngredients[existingIndex].quantity_per_serving = this.ingredientQuantity;
      } else {
        // Add new ingredient
        this.selectedIngredients.push({
          ingredient_id: this.selectedIngredientId,
          quantity_per_serving: this.ingredientQuantity
        });
      }
      
      // Reset dropdown selection
      this.selectedIngredientId = "";
      this.ingredientQuantity = null;
    },

    // NEW: Remove ingredient from recipe
    removeIngredientFromRecipe(index) {
      this.selectedIngredients.splice(index, 1);
    },

    // NEW: Helper methods to get ingredient details
    getIngredientName(id) {
      const ing = this.allIngredients.find(i => i.id === id);
      return ing ? ing.name : "";
    },

    getIngredientUnit(id) {
      const ing = this.allIngredients.find(i => i.id === id);
      return ing ? ing.unit : "";
    },

    getIngredientCalories(id) {
      const ing = this.allIngredients.find(i => i.id === id);
      return ing ? ing.calories_per_unit : 0;
    },

    loadIngredients() {
      fetch(window.api_ingredients)
      .then(res => res.json())
      .then(data => {
        this.allIngredients = data.ingredients.sort((a, b) => a.name.localeCompare(b.name));
      });
    },

    uploadImage(e) {
      const file = e.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append("image", file);
      fetch("/Recipe_Manager/upload", {
        method: "POST",
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          this.newRecipe.image = data.filename;
        } else {
          alert("Upload failed: " + data.error);
        }
      })
      .catch(err => {
        alert("Upload error: " + err);
      });
    }
  },

  computed: {
    // Show only ingredients that haven't been selected yet
    availableIngredients() {
      return this.allIngredients.filter(ing => 
        !this.selectedIngredients.some(sel => sel.ingredient_id === ing.id)
      );
    },

    totalCalories() {
      return this.selectedIngredients.reduce((sum, sel) => {
        const ing = this.allIngredients.find(i => i.id === sel.ingredient_id);
        return sum + (ing ? ing.calories_per_unit * sel.quantity_per_serving : 0);
      }, 0).toFixed(2);
    }
  },

  mounted() {
    this.loadIngredients();
  }
});