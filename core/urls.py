from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('career/', views.career, name='career'),
    path('contact/', views.contact, name='contact'),
 
    
    # احراز هویت
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # لاگین با پیامک (OTP)
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),  # حذف <str:phone>

    path('terms/', views.terms, name='terms'),
    path('news/', include('apps.news.urls')),
    path('dashboard/', include('apps.diagnosis.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)