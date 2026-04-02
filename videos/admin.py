from django.contrib import admin
from .models import VideoRequest
@admin.register(VideoRequest)
class VideoRequestAdmin(admin.ModelAdmin):
    list_display = ['user','platform','status','mode','created_at']
    list_filter = ['status','platform','mode']
