from django.contrib import admin
from .models import WorkoutPlan, UserPreferences,PaymentOption,Payment

@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'workout_date', 'email_sent', 'telegram_sent', 'discord_sent')
    list_filter = ('workout_date', 'email_sent', 'telegram_sent', 'discord_sent')
    search_fields = ('title', 'description')

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'telegram_chat_id', 'discord_user_id')

admin.site.register(PaymentOption)
admin.site.register(Payment)