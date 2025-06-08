from django.core.management.base import BaseCommand
from django.utils import timezone
from workout_app.models import WorkoutPlan, UserPreferences
from workout_app.utils import send_email, send_telegram, send_discord
import datetime

class Command(BaseCommand):
    help = 'Send workout notifications via email, Telegram, and Discord'
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        
        # Get workouts for today and tomorrow
        upcoming_workouts = WorkoutPlan.objects.filter(
            workout_date__in=[today, tomorrow]
        )
        
        sent_count = 0
        for workout in upcoming_workouts:
            try:
                user_prefs = UserPreferences.objects.get(user=workout.user)
                message = workout.format_message()
                subject = f"Workout Reminder: {workout.title} on {workout.workout_date}"
                
                # Send email if configured and not sent
                if workout.send_email and not workout.email_sent and user_prefs.email:
                    success, result = send_email(user_prefs.email, subject, message)
                    if success:
                        workout.email_sent = True
                        self.stdout.write(f"Email sent to {user_prefs.email}")
                        sent_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"Email failed: {result}"))
                
                # Send Telegram if configured and not sent
                if workout.send_telegram and not workout.telegram_sent and user_prefs.telegram_chat_id:
                    success, result = send_telegram(user_prefs.telegram_chat_id, message)
                    if success:
                        workout.telegram_sent = True
                        self.stdout.write(f"Telegram sent to chat {user_prefs.telegram_chat_id}")
                        sent_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"Telegram failed: {result}"))
                
                # Send Discord if configured and not sent
                if workout.send_discord and not workout.discord_sent and user_prefs.discord_user_id:
                    success, result = send_discord(user_prefs.discord_user_id, message)
                    if success:
                        workout.discord_sent = True
                        self.stdout.write(f"Discord sent to user {user_prefs.discord_user_id}")
                        sent_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"Discord failed: {result}"))
                
                # Save workout status
                workout.save()
                
            except UserPreferences.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"User {workout.user.username} has no preferences configured"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error processing workout {workout.id}: {str(e)}"
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f"Sent {sent_count} notifications for {upcoming_workouts.count()} workouts"
        ))