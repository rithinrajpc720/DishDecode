from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [('free', 'Free'), ('pro', 'Pro'), ('premium', 'Premium')]
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    generation_limit = models.IntegerField(default=5, help_text="Monthly generation limit. -1 for unlimited.")
    features = models.JSONField(default=list, help_text="List of feature strings")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['price_monthly']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    generations_used = models.IntegerField(default=0)
    last_reset = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        plan_name = self.plan.display_name if self.plan else 'Free'
        return f"{self.user.username} - {plan_name}"

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def active_plan(self):
        if self.plan and self.plan.name != 'free' and self.is_expired:
            return None
        return self.plan

    def _reset_if_needed(self):
        """Reset generation counter if a new month has started."""
        now = timezone.now()
        if now.month != self.last_reset.month or now.year != self.last_reset.year:
            self.generations_used = 0
            self.last_reset = now
            self.save(update_fields=['generations_used', 'last_reset'])

    def _get_limit(self):
        plan = self.active_plan
        if plan:
            return plan.generation_limit
        free = SubscriptionPlan.objects.filter(name='free').first()
        return free.generation_limit if free else 5

    def can_generate(self):
        limit = self._get_limit()
        if limit == -1:
            return True
        self._reset_if_needed()
        return self.generations_used < limit

    def remaining_generations(self):
        limit = self._get_limit()
        if limit == -1:
            return -1
        self._reset_if_needed()
        return limit - self.generations_used

    def increment_usage(self):
        self.generations_used += 1
        self.save(update_fields=['generations_used'])

class Payment(models.Model):
    STATUS_CHOICES = [('created', 'Created'), ('paid', 'Paid'), ('failed', 'Failed')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount} - {self.status}"

    class Meta:
        ordering = ['-created_at']
