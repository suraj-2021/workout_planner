import json
import uuid
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils import timezone

from .models import WorkoutPlan, UserPreferences, PaymentOption, Payment
from .forms import WorkoutPlanForm, ExerciseFormSetFactory, UserPreferencesForm
from .utils import get_payment_handler, format_currency

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    workouts = WorkoutPlan.objects.filter(user=request.user).order_by('workout_date')
    return render(request, 'workout_app/dashboard.html', {'workouts': workouts})

@login_required
def create_workout(request):
    if request.method == 'POST':
        workout_form = WorkoutPlanForm(request.POST)
        exercise_formset = ExerciseFormSetFactory(request.POST, prefix='exercises')
        
        if workout_form.is_valid() and exercise_formset.is_valid():
            # Save workout plan
            workout = workout_form.save(commit=False)
            workout.user = request.user
            
            # Process exercise data
            exercises = []
            for form in exercise_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    exercises.append({
                        'name': form.cleaned_data.get('exercise_name'),
                        'sets': form.cleaned_data.get('sets'),
                        'reps': form.cleaned_data.get('reps'),
                        'notes': form.cleaned_data.get('notes', '')
                    })
            
            # Save exercise data as JSON
            workout.exercises = json.dumps(exercises)
            workout.save()
            
            messages.success(request, "Workout plan created successfully!")
            return redirect('dashboard')
    else:
        workout_form = WorkoutPlanForm()
        exercise_formset = ExerciseFormSetFactory(prefix='exercises')
    
    return render(request, 'workout_app/create_workout.html', {
        'workout_form': workout_form,
        'exercise_formset': exercise_formset
    })

@login_required
def edit_workout(request, pk):
    workout = get_object_or_404(WorkoutPlan, pk=pk, user=request.user)
    
    if request.method == 'POST':
        workout_form = WorkoutPlanForm(request.POST, instance=workout)
        exercise_formset = ExerciseFormSetFactory(request.POST, prefix='exercises')
        
        if workout_form.is_valid() and exercise_formset.is_valid():
            # Save workout plan
            workout = workout_form.save(commit=False)
            
            # Process exercise data
            exercises = []
            for form in exercise_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    exercises.append({
                        'name': form.cleaned_data.get('exercise_name'),
                        'sets': form.cleaned_data.get('sets'),
                        'reps': form.cleaned_data.get('reps'),
                        'notes': form.cleaned_data.get('notes', '')
                    })
            
            # Save exercise data as JSON
            workout.exercises = json.dumps(exercises)
            workout.save()
            
            messages.success(request, "Workout plan updated successfully!")
            return redirect('dashboard')
    else:
        workout_form = WorkoutPlanForm(instance=workout)
        
        # Pre-populate exercise formset with existing exercises
        initial_exercises = []
        for exercise in workout.get_exercises():
            initial_exercises.append({
                'exercise_name': exercise['name'],
                'sets': exercise['sets'],
                'reps': exercise['reps'],
                'notes': exercise.get('notes', '')
            })
        
        exercise_formset = ExerciseFormSetFactory(
            initial=initial_exercises, 
            prefix='exercises'
        )
    
    return render(request, 'workout_app/edit_workout.html', {
        'workout_form': workout_form,
        'exercise_formset': exercise_formset,
        'workout': workout
    })

@login_required
def delete_workout(request, pk):
    workout = get_object_or_404(WorkoutPlan, pk=pk, user=request.user)
    
    if request.method == 'POST':
        workout.delete()
        messages.success(request, "Workout plan deleted successfully!")
        return redirect('dashboard')
    
    return render(request, 'workout_app/delete_workout.html', {'workout': workout})

@login_required
def user_preferences(request):
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Your preferences have been updated!")
            return redirect('dashboard')
    else:
        form = UserPreferencesForm(instance=preferences)
    
    return render(request, 'workout_app/preferences.html', {'form': form})

@login_required
def workout_detail(request, pk):
    workout = get_object_or_404(WorkoutPlan, pk=pk, user=request.user)
    exercises = workout.get_exercises()
    
    return render(request, 'workout_app/workout_detail.html', {
        'workout': workout,
        'exercises': exercises
    })

# Your existing views remain the same, add these new payment views:

def support_page(request):
    """Display support/donation page with payment options"""
    payment_options = PaymentOption.objects.filter(is_active=True)
    return render(request, 'workout_app/support.html', {
        'payment_options': payment_options
    })

@require_POST
def create_payment(request):
    """Create a payment order"""
    try:
        # Get form data
        payment_option_id = request.POST.get('payment_option_id')
        provider = request.POST.get('provider')
        supporter_name = request.POST.get('supporter_name', '')
        supporter_email = request.POST.get('supporter_email', '')
        supporter_message = request.POST.get('supporter_message', '')
        
        # Get payment option
        payment_option = get_object_or_404(PaymentOption, id=payment_option_id, is_active=True)
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            payment_option=payment_option,
            order_id=f"order_{uuid.uuid4().hex[:12]}",
            provider=provider,
            amount=payment_option.amount,
            supporter_name=supporter_name,
            supporter_email=supporter_email,
            supporter_message=supporter_message,
            status='pending'
        )
        
        # Get payment handler
        handler = get_payment_handler(provider)
        
        if provider == 'razorpay':
            success, result = handler.create_order(
                amount=float(payment.amount),
                receipt=payment.order_id
            )
            
            if success:
                payment.provider_data = {
                    'razorpay_order_id': result['id'],
                    'razorpay_amount': result['amount'],
                    'razorpay_currency': result['currency']
                }
                payment.save()
                
                return JsonResponse({
                    'success': True,
                    'provider': 'razorpay',
                    'order_id': result['id'],
                    'amount': result['amount'],
                    'currency': result['currency'],
                    'key': os.getenv('RAZORPAY_KEY_ID'),
                    'payment_id': payment.id,
                    'name': 'Workout Planner Support',
                    'description': payment_option.description,
                    'prefill': {
                        'name': supporter_name,
                        'email': supporter_email,
                    }
                })
            else:
                return JsonResponse({'success': False, 'error': result})
        
        elif provider == 'cashfree':
            customer_details = {
                "customer_id": f"customer_{payment.id}",
                "customer_name": supporter_name or "Anonymous",
                "customer_email": supporter_email or "noreply@example.com",
                "customer_phone": "9999999999"  # Required by Cashfree
            }
            
            return_url = request.build_absolute_uri(reverse('payment_success'))
            notify_url = request.build_absolute_uri(reverse('cashfree_webhook'))
            
            success, result = handler.create_order(
                amount=float(payment.amount),
                order_id=payment.order_id,
                customer_details=customer_details,
                return_url=return_url,
                notify_url=notify_url
            )
            
            if success:
                payment.provider_data = result
                payment.save()
                
                return JsonResponse({
                    'success': True,
                    'provider': 'cashfree',
                    'payment_session_id': result.get('payment_session_id'),
                    'order_id': payment.order_id,
                    'payment_url': result.get('payments', {}).get('url'),
                    'payment_id': payment.id
                })
            else:
                return JsonResponse({'success': False, 'error': result})
    
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def razorpay_callback(request):
    """Handle Razorpay payment callback"""
    try:
        # Get payment details from request
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        our_payment_id = request.POST.get('payment_id')
        
        # Get our payment record
        payment = get_object_or_404(Payment, id=our_payment_id, provider='razorpay')
        
        # Verify payment signature
        handler = get_payment_handler('razorpay')
        is_valid, message = handler.verify_payment(payment_id, order_id, signature)
        
        if is_valid:
            # Update payment status
            payment.payment_id = payment_id
            payment.status = 'success'
            payment.completed_at = timezone.now()
            payment.provider_data.update({
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            payment.save()
            
            messages.success(request, f'Thank you for your support! Payment of {format_currency(payment.amount)} was successful.')
            return redirect('payment_success')
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('payment_failed')
    
    except Exception as e:
        logger.error(f"Razorpay callback error: {str(e)}")
        messages.error(request, 'An error occurred while processing your payment.')
        return redirect('payment_failed')

@csrf_exempt
@require_POST
def cashfree_webhook(request):
    """Handle Cashfree webhook"""
    try:
        # Get webhook data
        payload = request.body.decode('utf-8')
        signature = request.headers.get('x-webhook-signature')
        timestamp = request.headers.get('x-webhook-timestamp')
        
        # Verify webhook signature
        handler = get_payment_handler('cashfree')
        if not handler.verify_webhook_signature(payload, signature, timestamp):
            return HttpResponse('Invalid signature', status=400)
        
        # Parse webhook data
        webhook_data = json.loads(payload)
        order_id = webhook_data.get('order', {}).get('order_id')
        
        if not order_id:
            return HttpResponse('Order ID not found', status=400)
        
        # Get payment record
        try:
            payment = Payment.objects.get(order_id=order_id, provider='cashfree')
        except Payment.DoesNotExist:
            return HttpResponse('Payment not found', status=404)
        
        # Update payment status based on webhook event
        event_type = webhook_data.get('type')
        if event_type == 'PAYMENT_SUCCESS':
            payment.status = 'success'
            payment.completed_at = timezone.now()
            payment.provider_data.update(webhook_data)
        elif event_type == 'PAYMENT_FAILED':
            payment.status = 'failed'
            payment.provider_data.update(webhook_data)
        
        payment.save()
        return HttpResponse('OK')
    
    except Exception as e:
        logger.error(f"Cashfree webhook error: {str(e)}")
        return HttpResponse('Error', status=500)

def payment_success(request):
    """Payment success page"""
    return render(request, 'workout_app/payment_success.html')

def payment_failed(request):
    """Payment failed page"""
    return render(request, 'workout_app/payment_failed.html')

@login_required
def payment_history(request):
    """Display user's payment history"""
    payments = Payment.objects.filter(
        user=request.user
    ).select_related('payment_option')
    
    return render(request, 'workout_app/payment_history.html', {
        'payments': payments
    })   
