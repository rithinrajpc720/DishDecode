from django.shortcuts import render
from django.views import View
from django.db.models import Avg
from videos.forms import VideoURLForm
from videos.models import VideoRequest
from recipes.models import RecipeResult, SavedRecipe
from django.contrib.auth.models import User

class HomeView(View):
    def get(self, request):
        form = VideoURLForm()
        total_videos = VideoRequest.objects.filter(status='completed').count()
        total_recipes = RecipeResult.objects.count()
        avg_confidence = RecipeResult.objects.aggregate(avg=Avg('confidence_score'))['avg']
        avg_confidence_pct = int((avg_confidence or 0.85) * 100)
        total_saved = SavedRecipe.objects.count()
        total_users = User.objects.count()
        return render(request, 'core/home.html', {
            'form': form,
            'total_videos': total_videos,
            'total_recipes': total_recipes,
            'avg_confidence': avg_confidence_pct,
            'total_saved': total_saved,
            'total_users': total_users,
        })
