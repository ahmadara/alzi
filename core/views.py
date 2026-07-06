from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
import random
from django.contrib.auth.models import User
from apps.news.models import NewsArticle
from apps.common.services.ghasedak_service import GhasedakService
from apps.accounts.models import UserProfile


# ========== صفحات اصلی ==========

def home(request):
    latest_news = NewsArticle.objects.filter(is_published=True)[:6]
    return render(request, 'home.html', {'latest_news': latest_news})

def about(request):
    return render(request, 'pages/about.html')

def career(request):
    return render(request, 'pages/career.html')

def contact(request):
    return render(request, 'pages/contact.html')

def terms(request):
    return render(request, 'pages/terms.html')



# ========== احراز هویت با رمز عبور ==========

def signin(request):
    next_url = request.GET.get('next', '') or request.POST.get('next', '')

    if request.user.is_authenticated:
        return redirect(next_url or 'home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f'خوش آمدید {user.username}!')
            return redirect(next_url or 'home')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')

    return render(request, 'pages/signin.html', {'next': next_url})


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        terms = request.POST.get('terms')

        if not terms:
            messages.error(request, 'پذیرش قوانین و مقررات الزامی است.')
            return render(request, 'pages/signup.html')

        if not email or not password:
            messages.error(request, 'ایمیل و رمز عبور الزامی هستند.')
            return render(request, 'pages/signup.html')

        if password != confirm_password:
            messages.error(request, 'رمز عبور و تکرار آن یکسان نیستند.')
            return render(request, 'pages/signup.html')

        if len(password) < 8:
            messages.error(request, 'رمز عبور باید حداقل ۸ کاراکتر باشد.')
            return render(request, 'pages/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'این ایمیل قبلاً ثبت شده است.')
            return render(request, 'pages/signup.html')

        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        name_parts = name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        UserProfile.objects.get_or_create(user=user)

        login(request, user)
        messages.success(request, f'خوش آمدید {first_name or username}! حساب شما ایجاد شد.')
        return redirect('dashboard:index')

    return render(request, 'pages/signup.html')


# ========== احراز هویت با پیامک (OTP) ==========

def send_otp(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if not phone or len(phone) < 11:
            messages.error(request, 'شماره موبایل معتبر وارد کنید')
            return render(request, 'accounts/send_otp.html')

        otp_code = str(random.randint(100000, 999999))

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
        entered_code = request.POST.get('code', '').strip()
        stored_code = request.session.get('otp_code')
        stored_phone = request.session.get('otp_phone')
        stored_time = request.session.get('otp_created_at')

        if not stored_code or not stored_phone:
            messages.error(request, 'جلسه منقضی شده است. دوباره تلاش کنید.')
            return redirect('send_otp')

        if stored_time:
            created_at = datetime.fromisoformat(stored_time)
            if timezone.now() - created_at > timedelta(minutes=5):
                messages.error(request, 'کد تأیید منقضی شده است.')
                return redirect('send_otp')

        if stored_code == entered_code:
            try:
                profile = UserProfile.objects.get(phone=stored_phone)
                user = profile.user
            except UserProfile.DoesNotExist:
                username = f"user_{stored_phone[-6:]}"
                user = User.objects.create_user(username=username, email=f"{stored_phone}@temp.com")
                UserProfile.objects.create(user=user, phone=stored_phone, phone_verified=True)

            request.session.pop('otp_code', None)
            request.session.pop('otp_phone', None)
            request.session.pop('otp_created_at', None)

            login(request, user)
            messages.success(request, f'خوش آمدید {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'کد وارد شده صحیح نیست.')

    phone = request.session.get('otp_phone', '')
    return render(request, 'accounts/verify_otp.html', {'phone': phone})
