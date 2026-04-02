import json
from django.db import models
from django.contrib.auth.models import User
from videos.models import VideoRequest

class RecipeResult(models.Model):
    RESULT_TYPE_CHOICES = [('extracted_recipe','Extracted Recipe'),('estimated_recipe','Estimated Recipe')]
    video_request = models.OneToOneField(VideoRequest, on_delete=models.CASCADE, related_name='recipe_result')
    dish_name = models.CharField(max_length=200)
    cuisine_type = models.CharField(max_length=100, blank=True)
    ingredients = models.TextField(default='[]')
    steps = models.TextField(default='[]')
    cooking_time = models.CharField(max_length=100)
    tools_used = models.TextField(default='[]')
    confidence_score = models.FloatField(default=0.0)
    ai_note = models.TextField(blank=True)
    result_type = models.CharField(max_length=30, choices=RESULT_TYPE_CHOICES, default='estimated_recipe')
    detected_language = models.CharField(max_length=50, blank=True, default='English')
    country_of_origin = models.CharField(max_length=100, blank=True, default='Unknown')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_ingredients(self):
        try: return json.loads(self.ingredients)
        except: return []

    def get_steps(self):
        try: return json.loads(self.steps)
        except: return []

    def get_tools(self):
        try: return json.loads(self.tools_used)
        except: return []

    def __str__(self):
        return self.dish_name

class SavedRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_recipes')
    recipe_result = models.ForeignKey(RecipeResult, on_delete=models.CASCADE, related_name='saves')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe_result')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} saved {self.recipe_result.dish_name}"
