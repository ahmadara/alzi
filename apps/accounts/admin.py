from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin
from .models import UserProfile

# خارج کردن User از ثبت قبلی
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "پروفایل"


@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_phone', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__phone']
    inlines = [UserProfileInline]
    
    def get_phone(self, obj):
        return obj.profile.phone if hasattr(obj, 'profile') and obj.profile else '-'
    get_phone.short_description = "شماره موبایل"
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخچه', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )