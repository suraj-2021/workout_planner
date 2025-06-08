from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_workout, name='create_workout'),
    path('edit/<int:pk>/', views.edit_workout, name='edit_workout'),
    path('delete/<int:pk>/', views.delete_workout, name='delete_workout'),
    path('detail/<int:pk>/', views.workout_detail, name='workout_detail'),
    path('preferences/', views.user_preferences, name='preferences'),
    
    # New Payment URLs
    path('support/', views.support_page, name='support_page'),
    path('payment/create/', views.create_payment, name='create_payment'),
    path('payment/razorpay/callback/', views.razorpay_callback, name='razorpay_callback'),
    path('payment/cashfree/webhook/', views.cashfree_webhook, name='cashfree_webhook'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('payments/', views.payment_history, name='payment_history'),
]