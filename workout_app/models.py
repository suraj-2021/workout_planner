from django.db import models
from django.contrib.auth.models import User
import json 
import uuid

class WorkoutPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    workout_date = models.DateField()
    
    # Workout details stored as JSON
    exercises = models.TextField(help_text="JSON format of exercises, sets, and reps")
    
    # Communication preferences and status
    send_email = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    
    send_telegram = models.BooleanField(default=False)
    telegram_sent = models.BooleanField(default=False)
    
    send_discord = models.BooleanField(default=False)
    discord_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.workout_date}"
    
    def get_exercises(self):
        """Convert JSON string to Python object"""
        if not self.exercises:
            return []
        return json.loads(self.exercises)
    
    def set_exercises(self, exercises_list):
        """Convert Python object to JSON string"""
        self.exercises = json.dumps(exercises_list)
    
    def format_message(self):
        """Format workout details as a message"""
        exercises = self.get_exercises()
        
        message = f"🏋️ WORKOUT: {self.title}\n"
        message += f"📅 DATE: {self.workout_date}\n"
        
        if self.description:
            message += f"\n{self.description}\n"
        
        message += "\n📋 EXERCISES:\n"
        
        for i, exercise in enumerate(exercises, 1):
            message += f"{i}. {exercise['name']}: {exercise['sets']} sets × {exercise['reps']} reps"
            if exercise.get('notes'):
                message += f" ({exercise['notes']})"
            message += "\n"
        
        message += "\nGet ready to crush it! 💪"
        
        return message


class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)
    discord_user_id = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"

# Add these new models to your workout_app/models.py

class PaymentOption(models.Model):
    PAYMENT_PROVIDERS = [
        ('razorpay', 'Razorpay'),
        ('cashfree', 'Cashfree'),
    ]
    
    name = models.CharField(max_length=100)  # e.g., "Buy me a coffee"
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount in INR
    provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDERS)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ₹{self.amount} ({self.provider})"

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_PROVIDERS = [
        ('razorpay', 'Razorpay'),
        ('cashfree', 'Cashfree'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    payment_option = models.ForeignKey(PaymentOption, on_delete=models.CASCADE)
    
    # Payment details
    order_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDERS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Supporter details (for anonymous donations)
    supporter_name = models.CharField(max_length=100, blank=True, null=True)
    supporter_email = models.EmailField(blank=True, null=True)
    supporter_message = models.TextField(blank=True, null=True)
    
    # Provider specific data
    provider_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.order_id} - ₹{self.amount} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']