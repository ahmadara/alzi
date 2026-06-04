from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import random

from .models import User  # اصلاح: از .models استفاده کن
from apps.common.services.ghasedak_service import GhasedakService

ghasedak = GhasedakService()


def send_otp(request):
    """مرحله 1: دریافت شماره موبایل و ارسال کد"""
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        
        if not phone or len(phone) < 11:
            messages.error(request, 'لطفاً شماره موبایل معتبر وارد کنید.')
            return render(request, 'accounts/send_otp.html')
        
        otp_code = str(random.randint(100000, 999999))
        
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                'username': phone,
                'phone': phone
            }
        )
        user.otp_code = otp_code
        user.otp_created_at = timezone.now()
        user.save()
        
        success, _ = ghasedak.send_otp(phone, otp_code)
        
        if success:
            messages.success(request, 'کد تأیید برای شما ارسال شد.')
        else:
            print(f"===== کد تأیید برای {phone} =====")
            print(f"کد: {otp_code}")
            print(f"=================================")
            messages.warning(request, f'پیامک ارسال نشد. کد آزمایشی: {otp_code}')
        
        return redirect('verify_otp', phone=phone)
    
    return render(request, 'accounts/send_otp.html')


def verify_otp(request, phone):
    """مرحله 2: تأیید کد و ورود کاربر"""
    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            messages.error(request, 'کاربری با این شماره یافت نشد.')
            return redirect('send_otp')
        
        if user.otp_created_at and timezone.now() - user.otp_created_at > timedelta(minutes=5):
            messages.error(request, 'کد تأیید منقضی شده است. دوباره تلاش کنید.')
            return redirect('send_otp')
        
        if user.otp_code == entered_code:
            user.otp_code = None
            user.otp_created_at = None
            user.phone_verified = True
            user.save()
            
            login(request, user)
            messages.success(request, f'خوش آمدید {user.get_full_name() or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'کد وارد شده صحیح نیست.')
    
    return render(request, 'accounts/verify_otp.html', {'phone': phone})