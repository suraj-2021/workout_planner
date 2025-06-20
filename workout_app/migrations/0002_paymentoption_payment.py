# Generated by Django 5.2.1 on 2025-06-05 02:38

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('provider', models.CharField(choices=[('razorpay', 'Razorpay'), ('cashfree', 'Cashfree')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(default=uuid.uuid4, max_length=100, unique=True)),
                ('payment_id', models.CharField(blank=True, max_length=100, null=True)),
                ('provider', models.CharField(choices=[('razorpay', 'Razorpay'), ('cashfree', 'Cashfree')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('supporter_name', models.CharField(blank=True, max_length=100, null=True)),
                ('supporter_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('supporter_message', models.TextField(blank=True, null=True)),
                ('provider_data', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('payment_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workout_app.paymentoption')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
