from django.db import models
from django.conf import settings
import jdatetime


class DiagnosisRecord(models.Model):
    RESULT_CHOICES = [
        ('CN', 'سالم'),
        ('MCI', 'اختلال خفیف شناختی'),
        ('AD', 'آلزایمر'),
        ('PENDING', 'در حال بررسی'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diagnoses',
        verbose_name="کاربر",
    )
    image = models.ImageField(upload_to='diagnosis/%Y/%m/', verbose_name="تصویر MRI")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='PENDING', verbose_name="نتیجه")
    confidence = models.FloatField(null=True, blank=True, verbose_name="درصد اطمینان")
    heatmap = models.ImageField(upload_to='heatmaps/%Y/%m/', null=True, blank=True, verbose_name="نقشه حرارتی")
    notes = models.TextField(blank=True, verbose_name="توضیحات پزشک")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ پردازش")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "تشخیص"
        verbose_name_plural = "تشخیص‌ها"

    def __str__(self):
        return f"{self.user.username} - {self.get_result_display()} - {self.jalali_created_at}"

    @property
    def jalali_created_at(self):
        import jdatetime
        jd = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jd.strftime("%Y/%m/%d %H:%M")

    def get_result_badge_class(self):
        mapping = {
            'CN': 'bg-green-100 text-green-700',
            'MCI': 'bg-yellow-100 text-yellow-700',
            'AD': 'bg-red-100 text-red-700',
            'PENDING': 'bg-gray-100 text-gray-600',
        }
        return mapping.get(self.result, 'bg-gray-100 text-gray-600')
