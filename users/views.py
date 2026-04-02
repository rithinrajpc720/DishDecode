from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import UserProfile, UserSubscription, SubscriptionPlan, Payment
from recipes.models import SavedRecipe, RecipeResult
from videos.models import VideoRequest
from django.db.models import Avg
import razorpay
from django.conf import settings as django_settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.utils import timezone

def _get_razorpay_client():
    return razorpay.Client(auth=(django_settings.RAZORPAY_KEY_ID, django_settings.RAZORPAY_KEY_SECRET))

class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated: return redirect('home')
        return render(request, 'users/register.html', {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, f"Welcome to DishDecode, {user.username}!")
            return redirect('home')
        return render(request, 'users/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated: return redirect('home')
        return render(request, 'users/login.html', {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.GET.get('next', 'home'))
        return render(request, 'users/login.html', {'form': form})

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('home')

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        # Fetching basic stats
        total_analyzed = VideoRequest.objects.filter(user=request.user).count()
        total_saved = SavedRecipe.objects.filter(user=request.user).count()
        avg_conf = RecipeResult.objects.filter(video_request__user=request.user).aggregate(avg=Avg('confidence_score'))['avg']
        avg_confidence = int((avg_conf or 0) * 100) if avg_conf else 0

        # Fetch Subscription Info
        sub, _ = UserSubscription.objects.get_or_create(user=request.user)
        plan = sub.active_plan
        remaining = sub.remaining_generations()
        
        # Dynamic Subscription Date (Next Reset or Billing)
        if plan and plan.name != 'free':
            next_date = sub.expires_at
            date_label = "Next Billing"
        else:
            # Free tier resets 30 days after last_reset
            next_date = sub.last_reset + timedelta(days=30)
            date_label = "Next Reset"

        # Fetch History
        saved_recipes = SavedRecipe.objects.filter(user=request.user).select_related('recipe_result')[:6]
        
        # Generation History with pre-calculated confidence percentages
        raw_history = RecipeResult.objects.filter(video_request__user=request.user).order_by('-created_at')[:6]
        gen_history = []
        for res in raw_history:
            # Adding a temporary attribute for the percentage
            res.conf_percent = int(res.confidence_score * 100)
            gen_history.append(res)

        return render(request, 'users/profile.html', {
            'total_analyzed': total_analyzed,
            'total_saved': total_saved,
            'avg_confidence': avg_confidence,
            'subscription': sub,
            'plan': plan,
            'remaining_generations': remaining,
            'next_date': next_date,
            'date_label': date_label,
            'saved_recipes': saved_recipes,
            'generation_history': gen_history,
        })

class PricingView(View):
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        current_plan = None
        if request.user.is_authenticated:
            sub, _ = UserSubscription.objects.get_or_create(user=request.user)
            active = sub.active_plan
            current_plan = active.name if active else 'free'
        return render(request, 'users/pricing.html', {
            'plans': plans,
            'current_plan': current_plan,
        })

@method_decorator(login_required, name='dispatch')
class CreateOrderView(View):
    def post(self, request, plan_name):
        plan = SubscriptionPlan.objects.filter(name=plan_name, is_active=True).first()
        if not plan or plan.price_monthly <= 0:
            messages.error(request, "Invalid plan selected.")
            return redirect('pricing')

        client = _get_razorpay_client()
        if not django_settings.RAZORPAY_KEY_ID or not django_settings.RAZORPAY_KEY_SECRET:
            messages.error(request, "Payment gateway is not configured. Please contact the administrator.")
            return redirect('pricing')

        amount_paise = int(plan.price_monthly * 100)
        order_data = {
            'amount': amount_paise,
            'currency': 'INR',
            'notes': {
                'plan_name': plan.name,
                'user_id': str(request.user.id),
            }
        }
        try:
            order = client.order.create(data=order_data)
        except Exception:
            messages.error(request, "Payment gateway error. Please try again later.")
            return redirect('pricing')
        Payment.objects.create(
            user=request.user,
            plan=plan,
            razorpay_order_id=order['id'],
            amount=plan.price_monthly,
        )
        return render(request, 'users/checkout.html', {
            'plan': plan,
            'order': order,
            'razorpay_key': django_settings.RAZORPAY_KEY_ID,
            'user': request.user,
        })

@method_decorator(login_required, name='dispatch')
class PaymentCallbackView(View):
    def post(self, request):
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')

        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id, user=request.user)
        except Payment.DoesNotExist:
            messages.error(request, "Payment not found.")
            return redirect('pricing')

        # Prevent duplicate processing
        if payment.status == 'paid':
            messages.info(request, "This payment has already been processed.")
            return redirect('profile')

        client = _get_razorpay_client()
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            payment.status = 'failed'
            payment.save()
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('pricing')

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'paid'
        payment.save()

        # Activate subscription
        sub, _ = UserSubscription.objects.get_or_create(user=payment.user)
        sub.plan = payment.plan
        sub.started_at = timezone.now()
        sub.expires_at = timezone.now() + timedelta(days=30)
        sub.generations_used = 0
        sub.last_reset = timezone.now()
        sub.save()

        messages.success(request, f"Payment successful! You're now on the {payment.plan.display_name} plan.")
        return redirect('profile')
