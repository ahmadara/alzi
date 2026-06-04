from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import random
from django.contrib.auth.models import User  # مدل پیش‌فرض Django
from apps.news.models import NewsArticle
from apps.common.services.ghasedak_service import GhasedakService
from apps.accounts.models import UserProfile
from datetime import datetime

# ========== صفحات اصلی سایت ==========

def home(request):
    latest_news = NewsArticle.objects.filter(is_published=True)[:6]
    return render(request, 'home.html', {'latest_news': latest_news})

def about(request):
    return render(request, 'pages/about.html')

def features(request):
    return render(request, 'pages/features.html')

def pricing(request):
    return render(request, 'pages/pricing.html')

def career(request):
    return render(request, 'pages/career.html')

def contact(request):
    return render(request, 'pages/contact.html')

def terms(request):
    return render(request, 'pages/terms.html')

def how_it_works(request):
    return render(request, 'pages/how_it_works.html')


# ========== احراز هویت با رمز عبور ==========

def signin(request):
    if request.user.is_authenticated:
        return redirect('/admin/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f'خوش آمدید {user.username}!')
            return redirect('/admin/')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    
    return render(request, 'pages/signin.html')


def signup(request):
    return render(request, 'pages/signup.html')


# ========== احراز هویت با پیامک (OTP) - نسخه نهایی ==========

def send_otp(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if not phone or len(phone) < 11:
            messages.error(request, 'شماره موبایل معتبر وارد کنید')
            return render(request, 'accounts/send_otp.html')
        
        otp_code = str(random.randint(100000, 999999))
        
        # ذخیره در session
        request.session['otp_code'] = otp_code
        request.session['otp_phone'] = phone
        request.session['otp_created_at'] = timezone.now().isoformat()
        
        ghasedak = GhasedakService()
        success, _ = ghasedak.send_otp(phone, otp_code)
        
        if success:
            messages.success(request, 'کد تأیید ارسال شد')
        else:
            messages.warning(request, f'کد آزمایشی: {otp_code}')
        
        return redirect('verify_otp')
    
    return render(request, 'accounts/send_otp.html')


def verify_otp(request):
    if request.method == 'POST':
        entered_code = request.POST.get('code', '')
        stored_code = request.session.get('otp_code')
        stored_phone = request.session.get('otp_phone')
        stored_time = request.session.get('otp_created_at')
        
        if not stored_code or not stored_phone:
            messages.error(request, 'جلسه منقضی شده است')
            return redirect('send_otp')
        
        if stored_time:
            created_at = datetime.fromisoformat(stored_time)
            if timezone.now() - created_at > timedelta(minutes=5):
                messages.error(request, 'کد منقضی شده')
                return redirect('send_otp')
        
        if stored_code == entered_code:
            # پیدا کردن کاربر با شماره موبایل در پروفایل
            from apps.accounts.models import UserProfile
            
            try:
                profile = UserProfile.objects.get(phone=stored_phone)
                user = profile.user
                created = False
            except UserProfile.DoesNotExist:
                # ساخت کاربر جدید
                username = f"user_{stored_phone[-6:]}"
                user = User.objects.create_user(
                    username=username,
                    email=f"{stored_phone}@temp.com"
                )
                # ساخت پروفایل با شماره موبایل
                UserProfile.objects.create(user=user, phone=stored_phone, phone_verified=True)
                created = True
            
            # پاک کردن session
            del request.session['otp_code']
            del request.session['otp_phone']
            if 'otp_created_at' in request.session:
                del request.session['otp_created_at']
            
            login(request, user)
            messages.success(request, f'خوش آمدید {user.username}')
            return redirect('home')
        else:
            messages.error(request, 'کد اشتباه است')
    
    phone = request.session.get('otp_phone', '')
    return render(request, 'accounts/verify_otp.html', {'phone': phone})
    if request.method == 'POST':
        entered_code = request.POST.get('code', '')
        stored_code = request.session.get('otp_code')
        stored_phone = request.session.get('otp_phone')
        stored_time = request.session.get('otp_created_at')
        
        if not stored_code or not stored_phone:
            messages.error(request, 'جلسه منقضی شده')
            return redirect('send_otp')
        
        # بررسی انقضا (5 دقیقه)
        if stored_time:
            created_at = datetime.fromisoformat(stored_time)
            if timezone.now() - created_at > timedelta(minutes=5):
                messages.error(request, 'کد منقضی شده')
                return redirect('send_otp')
        
        if stored_code == entered_code:
            # ساخت یا پیدا کردن کاربر
            user, created = User.objects.get_or_create(
                username=stored_phone,
                defaults={'email': f"{stored_phone}@temp.com"}
            )
            
            # پاک کردن session
            del request.session['otp_code']
            del request.session['otp_phone']
            if 'otp_created_at' in request.session:
                del request.session['otp_created_at']
            
            login(request, user)
            messages.success(request, f'خوش آمدید {user.username}')
            return redirect('home')
        else:
            messages.error(request, 'کد اشتباه است')
    
    phone = request.session.get('otp_phone', '')
    return render(request, 'accounts/verify_otp.html', {'phone': phone})
    """مرحله 2: تأیید کد و ورود کاربر"""
    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        
        stored_code = request.session.get('otp_code')
        stored_phone = request.session.get('otp_phone')
        stored_time = request.session.get('otp_created_at')
        
        if not stored_code or not stored_phone:
            messages.error(request, 'جلسه منقضی شده است. دوباره تلاش کنید.')
            return redirect('send_otp')
        
        if stored_time:
            created_at = timezone.datetime.fromisoformat(stored_time)
            if timezone.now() - created_at > timedelta(minutes=5):
                messages.error(request, 'کد تأیید منقضی شده است.')
                return redirect('send_otp')
        
        if stored_code == entered_code:
            # پیدا کردن کاربر با این شماره
            try:
                profile = UserProfile.objects.get(phone=stored_phone)
                user = profile.user
            except UserProfile.DoesNotExist:
                # ساخت کاربر جدید
                username = f"user_{stored_phone[-6:]}"
                user = User.objects.create_user(
                    username=username,
                    email=f"{stored_phone}@temp.com",
                    first_name='کاربر',
                    last_name='گرامی'
                )
                UserProfile.objects.create(user=user, phone=stored_phone, phone_verified=True)
            
            # پاک کردن session
            del request.session['otp_code']
            del request.session['otp_phone']
            if 'otp_created_at' in request.session:
                del request.session['otp_created_at']
            
            login(request, user)
            messages.success(request, f'خوش آمدید {user.get_full_name() or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'کد وارد شده صحیح نیست.')
    
    phone = request.session.get('otp_phone', '')
    return render(request, 'accounts/verify_otp.html', {'phone': phone})

    """مرحله 2: تأیید کد و ورود کاربر"""
    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        
        # دریافت از session
        stored_code = request.session.get('otp_code')
        stored_phone = request.session.get('otp_phone')
        stored_time = request.session.get('otp_created_at')
        
        if not stored_code or not stored_phone:
            messages.error(request, 'جلسه منقضی شده است. دوباره تلاش کنید.')
            return redirect('send_otp')
        
        # بررسی انقضای کد (5 دقیقه)
        if stored_time:
            created_at = timezone.datetime.fromisoformat(stored_time)
            if timezone.now() - created_at > timedelta(minutes=5):
                messages.error(request, 'کد تأیید منقضی شده است. دوباره تلاش کنید.')
                return redirect('send_otp')
        
        if stored_code == entered_code:
            # پیدا کردن یا ساخت کاربر با این شماره
            user, created = User.objects.get_or_create(
                username=stored_phone,
                defaults={
                    'email': f"{stored_phone}@temp.com",
                    'first_name': 'کاربر',
                    'last_name': 'گرامی'
                }
            )
            
            # پاک کردن session
            del request.session['otp_code']
            del request.session['otp_phone']
            if 'otp_created_at' in request.session:
                del request.session['otp_created_at']
            
            login(request, user)
            messages.success(request, f'خوش آمدید {user.get_full_name() or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'کد وارد شده صحیح نیست.')
    
    phone = request.session.get('otp_phone', '')
    return render(request, 'accounts/verify_otp.html', {'phone': phone})