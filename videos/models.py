from django.db import models
from django.contrib.auth.models import User

class VideoRequest(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('processing','Processing'),('completed','Completed'),('failed','Failed')]
    MODE_CHOICES = [('process_based','Process Based'),('recognition_based','Recognition Based')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_requests')
    video_url = models.URLField(max_length=500)
    platform = models.CharField(max_length=50, default='youtube')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mode = models.CharField(max_length=30, choices=MODE_CHOICES, default='recognition_based')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.video_url[:50]}"

    class Meta:
        ordering = ['-created_at']
