from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import display
from .models import UserProfile

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "پروفایل کاربر"
    extra = 0
    fields = ['phone', 'phone_verified']


@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    list_display = [
        'username', 'get_full_name_display', 'email',
        'get_phone', 'display_is_active', 'display_is_staff', 'date_joined'
    ]
    list_filter = ['is_staff', 'is_active', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__phone']
    ordering = ['-date_joined']
    inlines = [UserProfileInline]
    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff']
    list_per_page = 30

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email')}),
        ('دسترسی‌ها', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('تاریخچه', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ['last_login', 'date_joined']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    @display(description="نام کامل")
    def get_full_name_display(self, obj):
        return obj.get_full_name() or '-'

    @display(description="شماره موبایل")
    def get_phone(self, obj):
        try:
            return obj.profile.phone or '-'
        except Exception:
            return '-'

    @display(boolean=True, description="فعال")
    def display_is_active(self, obj):
        return obj.is_active

    @display(boolean=True, description="مدیر")
    def display_is_staff(self, obj):
        return obj.is_staff

    @admin.action(description="فعال‌سازی کاربران انتخاب‌شده")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} کاربر فعال شد.")

    @admin.action(description="غیرفعال‌سازی کاربران انتخاب‌شده")
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} کاربر غیرفعال شد.")

    @admin.action(description="تبدیل به مدیر")
    def make_staff(self, request, queryset):
        count = queryset.update(is_staff=True)
        self.message_user(request, f"{count} کاربر به مدیر تبدیل شد.")

    @admin.action(description="حذف دسترسی مدیر")
    def remove_staff(self, request, queryset):
        count = queryset.update(is_staff=False)
        self.message_user(request, f"دسترسی مدیر از {count} کاربر حذف شد.")


