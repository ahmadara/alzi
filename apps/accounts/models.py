from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="شماره موبایل")
    phone_verified = models.BooleanField(default=False, verbose_name="شماره تأیید شده؟")
    
    def __str__(self):
        return f"{self.user.username} - {self.phone or 'بدون شماره'}"
    
    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل کاربران"