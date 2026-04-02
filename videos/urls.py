from django.urls import path
from .views import SubmitVideoView, AnalyzeVideoView, ProcessVideoView
urlpatterns = [
    path('submit/', SubmitVideoView.as_view(), name='submit_video'),
    path('analyze/<int:pk>/', AnalyzeVideoView.as_view(), name='analyze_video'),
    path('process/<int:pk>/', ProcessVideoView.as_view(), name='process_video'),
]
