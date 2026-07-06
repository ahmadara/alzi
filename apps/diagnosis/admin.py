from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import DiagnosisRecord


@admin.register(DiagnosisRecord)
class DiagnosisRecordAdmin(ModelAdmin):
    list_display = [
        'user', 'display_result', 'display_confidence',
        'jalali_created_at_display', 'has_heatmap'
    ]
    list_filter = ['result', 'created_at']
    search_fields = [
        'user__username', 'user__first_name',
        'user__last_name', 'user__profile__phone'
    ]
    readonly_fields = ['jalali_created_at_display', 'created_at']
    ordering = ['-created_at']
    list_per_page = 30
    actions = ['mark_cn', 'mark_mci', 'mark_ad', 'mark_pending']

    fieldsets = (
        ('اطلاعات بیمار', {
            'fields': ('user',)
        }),
        ('تصویر MRI', {
            'fields': ('image', 'heatmap')
        }),
        ('نتیجه تشخیص', {
            'fields': ('result', 'confidence', 'notes'),
            'description': 'CN = سالم | MCI = اختلال خفیف شناختی | AD = آلزایمر'
        }),
        ('زمان ثبت', {
            'fields': ('jalali_created_at_display',)
        }),
    )

    @display(
        label={
            'سالم': 'success',
            'اختلال خفیف شناختی': 'warning',
            'آلزایمر': 'danger',
            'در حال بررسی': 'info',
        },
        description="نتیجه"
    )
    def display_result(self, obj):
        return obj.get_result_display()

    @display(description="اطمینان مدل")
    def display_confidence(self, obj):
        if obj.confidence is None:
            return "—"
        return f"{obj.confidence:.1f}٪"

    @display(description="تاریخ (شمسی)", ordering="created_at")
    def jalali_created_at_display(self, obj):
        return obj.jalali_created_at

    @display(boolean=True, description="نقشه حرارتی")
    def has_heatmap(self, obj):
        return bool(obj.heatmap)

    @admin.action(description="علامت‌گذاری: سالم (CN)")
    def mark_cn(self, request, queryset):
        count = queryset.update(result='CN')
        self.message_user(request, f"{count} مورد به 'سالم' تغییر یافت.")

    @admin.action(description="علامت‌گذاری: اختلال خفیف شناختی (MCI)")
    def mark_mci(self, request, queryset):
        count = queryset.update(result='MCI')
        self.message_user(request, f"{count} مورد به 'اختلال خفیف شناختی' تغییر یافت.")

    @admin.action(description="علامت‌گذاری: آلزایمر (AD)")
    def mark_ad(self, request, queryset):
        count = queryset.update(result='AD')
        self.message_user(request, f"{count} مورد به 'آلزایمر' تغییر یافت.")

    @admin.action(description="بازگشت به حال بررسی (PENDING)")
    def mark_pending(self, request, queryset):
        count = queryset.update(result='PENDING')
        self.message_user(request, f"{count} مورد به 'در حال بررسی' تغییر یافت.")
