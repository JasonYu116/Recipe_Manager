new Vue({
    el: "#ingredient-app",
    data: {
        ingredients: [],
        search: "",
        newIngredient: {
            name: "",
            unit: "",
            calories_per_unit: null,
            description: ""
        },
        error: null
    },
    methods: {
        loadIngredients() {
            fetch(`${window.api_base}?search=${encodeURIComponent(this.search)}`)
                .then(res => res.json())
                .then(data => {
                    this.ingredients = data.ingredients;
                });
        },
        addIngredient() {
            this.error = null;
            fetch(window.api_base, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.newIngredient)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.newIngredient = { name: "", unit: "", calories_per_unit: null, description: "" };
                    this.loadIngredients();
                } else {
                    this.error = data.error;
                }
            });
        },
        deleteIngredient(id) {
            fetch(`${window.api_base}/${id}`, {
                method: "DELETE"
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.loadIngredients();
                }
            });
        }
    },
    mounted() {
        this.loadIngredients();
    }
});
