// static/js/recipe.js
document.addEventListener('DOMContentLoaded', function () {
  new Vue({
    el: "#recipe-app",
    data: {
      recipes: [],
      search: "",
      typeFilter: "",
      user_id: window.user_id,
      editingRecipe: null,
      editForm: {
        name: "",
        type: "",
        description: "",
        servings: 1,
        instruction_steps: ""
      },
      showImageModal: false,
      currentModalImage: "",
      currentModalImageName: ""
    },
    computed: {
      filteredRecipes() {
        let filtered = this.recipes;
        
        // Filter by type if selected
        if (this.typeFilter) {
          filtered = filtered.filter(r => r.type === this.typeFilter);
        }
        
        // Filter by search term if provided
        if (this.search) {
          const q = this.search.toLowerCase();
          filtered = filtered.filter(r =>
            r.name.toLowerCase().includes(q) ||
            r.type.toLowerCase().includes(q) ||
            r.description.toLowerCase().includes(q)
          );
        }
        
        return filtered;
      }
    },
    methods: {
      loadRecipes() {
        // Load all recipes from the server, then filter on the frontend
        fetch(`/Recipe_Manager/api/recipes`)
          .then(res => res.json())
          .then(data => {
            this.recipes = data.recipes.map(r => {
              if (!r.image) return { ...r, imageUrl: null };
              const isAbsolute = r.image.startsWith('http://') || r.image.startsWith('https://');
              return {
                ...r,
		imageUrl: isAbsolute ? r.image : `/Recipe_Manager/uploads/${r.image}`

              };
            });
          })
          .catch(error => {
            console.error('Error loading recipes:', error);
          });
      },
      showFullImage(src, name) {
        this.currentModalImage = src;
        this.currentModalImageName = name;
        this.showImageModal = true;
        document.body.classList.add("modal-open");
      },
      closeImageModal() {
        this.showImageModal = false;
        document.body.classList.remove("modal-open");
      },
      editRecipe(recipe) {
        this.editingRecipe = recipe.id;
        this.editForm = {
          name: recipe.name,
          type: recipe.type,
          description: recipe.description,
          servings: recipe.servings,
          instruction_steps: recipe.instruction_steps
        };
      },
      cancelEdit() {
        this.editingRecipe = null;
        this.editForm = {
          name: "",
          type: "",
          description: "",
          servings: 1,
          instruction_steps: ""
        };
      },
      saveRecipe(recipeId) {
        if (
          !this.editForm.name.trim() ||
          !this.editForm.type ||
          !this.editForm.description.trim() ||
          !this.editForm.instruction_steps.trim()
        ) {
          alert("Please fill in all fields");
          return;
        }
        if (this.editForm.servings < 1) {
          alert("Servings must be at least 1");
          return;
        }
        fetch(`${window.api_base}/${recipeId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: this.editForm.name.trim(),
            type: this.editForm.type,
            description: this.editForm.description.trim(),
            servings: parseInt(this.editForm.servings, 10),
            instruction_steps: this.editForm.instruction_steps.trim()
          })
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              this.cancelEdit();
              this.loadRecipes();
            } else {
              alert("Error updating recipe: " + (data.error || "Unknown error"));
            }
          })
          .catch(() => {
            alert("Error updating recipe. Please try again.");
          });
      },
      deleteRecipe(recipe_id) {
        if (!confirm("Are you sure you want to delete this recipe?")) return;
        fetch(`${window.api_base}/${recipe_id}`, { method: "DELETE" })
          .then(res => res.json())
          .then(data => {
            if (data.success) this.loadRecipes();
            else alert("Error deleting recipe: " + (data.error || "Unknown error"));
          })
          .catch(() => {
            alert("Error deleting recipe. Please try again.");
          });
      },
      copyRecipe(r) {
        const text = `${r.name} (${r.type})\n\n${r.description}\n\nInstructions:\n${r.instruction_steps}`;
        navigator.clipboard.writeText(text);
      },
      likeRecipe(recipe) {
        fetch(`/Recipe_Manager/api/recipes/like/${recipe.id}`, {
          method: "POST"
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              // Update the recipe in the local array
              const recipeIndex = this.recipes.findIndex(r => r.id === recipe.id);
              if (recipeIndex !== -1) {
                this.$set(this.recipes[recipeIndex], 'likes', data.likes);
              }
            } else {
              alert("Error liking recipe: " + (data.error || "Unknown error"));
            }
          })
          .catch(error => {
            console.error('Error liking recipe:', error);
            alert("Error liking recipe. Please try again.");
          });
      },
      dislikeRecipe(recipe) {
        fetch(`/Recipe_Manager/api/recipes/dislike/${recipe.id}`, {
          method: "POST"
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              // Update the recipe in the local array
              const recipeIndex = this.recipes.findIndex(r => r.id === recipe.id);
              if (recipeIndex !== -1) {
                this.$set(this.recipes[recipeIndex], 'dislikes', data.dislikes);
              }
            } else {
              alert("Error disliking recipe: " + (data.error || "Unknown error"));
            }
          })
          .catch(error => {
            console.error('Error disliking recipe:', error);
            alert("Error disliking recipe. Please try again.");
          });
      },
      
      rateRecipe(recipeId, score) {
        if (!window.user_id) {
          alert("You must be logged in to rate.");
          return;
        }
        fetch(`${window.api_base}/rate_recipe`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            recipe_id: recipeId,
            rating: score,
          }),
        })
        .then(response => response.json())
        .then(data => {
          // update recipe user_rating
          const recipe = this.filteredRecipes.find(r => r.id === recipeId);
          if (recipe) {
            recipe.user_rating = score;
          }
        })
        .catch(error => {
          console.error("Rating failed:", error);
        });
      },

    
    },
    
    mounted() {
      this.loadRecipes();
    }
  });
});
