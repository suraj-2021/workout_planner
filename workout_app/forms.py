from django import forms
from .models import WorkoutPlan, UserPreferences

class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ['email', 'telegram_chat_id', 'discord_user_id']
        
class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ['title', 'description', 'workout_date', 'send_email', 'send_telegram', 'send_discord']
        widgets = {
            'workout_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ExerciseFormSet(forms.Form):
    exercise_name = forms.CharField(max_length=100, label="Exercise Name")
    sets = forms.IntegerField(min_value=1, initial=3)
    reps = forms.IntegerField(min_value=1, initial=10)
    notes = forms.CharField(max_length=200, required=False)
    
ExerciseFormSetFactory = forms.formset_factory(ExerciseFormSet, extra=3, can_delete=True)
