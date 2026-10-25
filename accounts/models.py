from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('AUDITOR', 'Auditor'),
        ('ANALYST', 'Analyst'),
        ('VIEWER', 'Viewer / Management'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='AUDITOR')
    department = models.CharField(max_length=100, default='Internal Audit')
    title = models.CharField(max_length=100, default='Senior Auditor')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
