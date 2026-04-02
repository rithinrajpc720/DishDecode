from django.urls import path
from .views import RecipeResultView, SaveRecipeView, RecipeHistoryView, RecipeDetailView
urlpatterns = [
    path('result/<int:pk>/', RecipeResultView.as_view(), name='recipe_result'),
    path('save/<int:pk>/', SaveRecipeView.as_view(), name='save_recipe'),
    path('history/', RecipeHistoryView.as_view(), name='recipe_history'),
    path('detail/<int:pk>/', RecipeDetailView.as_view(), name='recipe_detail'),
]
