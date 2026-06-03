from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from apps.news.models import NewsArticle

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

def signin(request):
    if request.user.is_authenticated:
        return redirect('/admin/')  # تغییر به ادمین
    
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
            return redirect('/admin/')  # تغییر به ادمین
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    
    return render(request, 'pages/signin.html')
def signup(request):
    return render(request, 'pages/signup.html')

def terms(request):
    return render(request, 'pages/terms.html')

def how_it_works(request):
    return render(request, 'pages/how_it_works.html')