import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.contrib import messages
from .forms import VideoURLForm
from .models import VideoRequest
from recipes.models import RecipeResult
from ai_engine.services.recipe_generator import validate_video_url, detect_platform, generate_recipe_from_url
from users.models import UserSubscription

@method_decorator(login_required, name='dispatch')
class SubmitVideoView(View):
    def post(self, request):
        # Check generation limit
        sub, _ = UserSubscription.objects.get_or_create(user=request.user)
        if not sub.can_generate():
            messages.error(request, "You've reached your monthly generation limit. Upgrade your plan for more!")
            return redirect('pricing')

        form = VideoURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['video_url']
            is_valid, platform = validate_video_url(url)
            if not is_valid:
                messages.error(request, "Please provide a valid YouTube or Instagram Reels URL.")
                return redirect('home')
            video_req = VideoRequest.objects.create(
                user=request.user, video_url=url,
                platform=platform or 'unknown', status='processing'
            )
            return redirect('analyze_video', pk=video_req.pk)
        messages.error(request, "Invalid URL. Please try again.")
        return redirect('home')

@method_decorator(login_required, name='dispatch')
class AnalyzeVideoView(View):
    def get(self, request, pk):
        video_req = get_object_or_404(VideoRequest, pk=pk, user=request.user)
        if video_req.status == 'completed':
            return redirect('recipe_result', pk=pk)
        return render(request, 'videos/analyze.html', {'video_req': video_req})

@method_decorator(login_required, name='dispatch')
class ProcessVideoView(View):
    def post(self, request, pk):
        video_req = get_object_or_404(VideoRequest, pk=pk, user=request.user)
        if video_req.status == 'completed':
            return JsonResponse({'status': 'completed', 'redirect': f'/recipes/result/{pk}/'})
        try:
            result_data = generate_recipe_from_url(video_req.video_url)
            video_req.mode = 'process_based' if result_data['result_type'] == 'extracted_recipe' else 'recognition_based'
            video_req.status = 'completed'
            video_req.save()
            RecipeResult.objects.create(
                video_request=video_req,
                dish_name=result_data['dish_name'],
                cuisine_type=result_data['cuisine_type'],
                ingredients=json.dumps(result_data['ingredients']),
                steps=json.dumps(result_data['steps']),
                cooking_time=result_data['cooking_time'],
                tools_used=json.dumps(result_data['tools_used']),
                confidence_score=result_data['confidence_score'],
                ai_note=result_data['ai_note'],
                result_type=result_data['result_type'],
            )
            # Increment generation usage
            sub, _ = UserSubscription.objects.get_or_create(user=request.user)
            sub.increment_usage()
            return JsonResponse({'status': 'completed', 'redirect': f'/recipes/result/{pk}/'})
        except Exception as e:
            video_req.status = 'failed'
            video_req.save()
            return JsonResponse({'status': 'failed', 'error': str(e)})

