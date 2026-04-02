from django.contrib import admin
from .models import RecipeResult, SavedRecipe
@admin.register(RecipeResult)
class RecipeResultAdmin(admin.ModelAdmin):
    list_display = ['dish_name','cuisine_type','result_type','confidence_score','created_at']
@admin.register(SavedRecipe)
class SavedRecipeAdmin(admin.ModelAdmin):
    list_display = ['user','recipe_result','saved_at']
