from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from .models import RecipeResult, SavedRecipe
from videos.models import VideoRequest

@method_decorator(login_required, name='dispatch')
class RecipeResultView(View):
    def get(self, request, pk):
        video_req = get_object_or_404(VideoRequest, pk=pk, user=request.user)
        recipe = get_object_or_404(RecipeResult, video_request=video_req)
        is_saved = SavedRecipe.objects.filter(user=request.user, recipe_result=recipe).exists()
        return render(request, 'recipes/result.html', {
            'recipe': recipe, 'video_req': video_req, 'is_saved': is_saved,
        })

@method_decorator(login_required, name='dispatch')
class SaveRecipeView(View):
    def post(self, request, pk):
        recipe = get_object_or_404(RecipeResult, pk=pk, video_request__user=request.user)
        saved, created = SavedRecipe.objects.get_or_create(user=request.user, recipe_result=recipe)
        if not created:
            saved.delete()
            return JsonResponse({'status': 'unsaved'})
        return JsonResponse({'status': 'saved'})

@method_decorator(login_required, name='dispatch')
class RecipeHistoryView(View):
    def get(self, request):
        q = request.GET.get('q', '')
        filter_type = request.GET.get('type', '')
        recipes = RecipeResult.objects.filter(video_request__user=request.user).select_related('video_request')
        if q:
            recipes = recipes.filter(Q(dish_name__icontains=q) | Q(cuisine_type__icontains=q))
        if filter_type:
            recipes = recipes.filter(result_type=filter_type)
        recipes = recipes.order_by('-created_at')
        saved_ids = set(SavedRecipe.objects.filter(user=request.user).values_list('recipe_result_id', flat=True))
        return render(request, 'recipes/history.html', {
            'recipes': recipes, 'saved_ids': saved_ids,
            'q': q, 'filter_type': filter_type,
        })

@method_decorator(login_required, name='dispatch')
class RecipeDetailView(View):
    def get(self, request, pk):
        recipe = get_object_or_404(RecipeResult, pk=pk, video_request__user=request.user)
        is_saved = SavedRecipe.objects.filter(user=request.user, recipe_result=recipe).exists()
        return render(request, 'recipes/result.html', {
            'recipe': recipe, 'video_req': recipe.video_request, 'is_saved': is_saved,
        })
