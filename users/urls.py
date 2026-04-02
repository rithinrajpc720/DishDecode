from django.urls import path
from .views import RegisterView, LoginView, LogoutView, ProfileView, PricingView, CreateOrderView, PaymentCallbackView
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('pricing/', PricingView.as_view(), name='pricing'),
    path('checkout/<str:plan_name>/', CreateOrderView.as_view(), name='create_order'),
    path('payment/callback/', PaymentCallbackView.as_view(), name='payment_callback'),
]
