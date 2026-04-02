from django.contrib import admin
from .models import UserProfile, SubscriptionPlan, UserSubscription, Payment

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user','created_at']

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'price_monthly', 'generation_limit', 'is_active']

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'generations_used', 'started_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'status', 'razorpay_order_id', 'created_at']
    list_filter = ['status']
