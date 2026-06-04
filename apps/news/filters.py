from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
import jdatetime
from datetime import datetime

class JalaliDateRangeFilter(SimpleListFilter):
    title = _('بازه تاریخ (شمسی)')
    parameter_name = 'jalali_date_range'
    
    def lookups(self, request, model_admin):
        return (
            ('today', 'امروز'),
            ('yesterday', 'دیروز'),
            ('last_7_days', '۷ روز گذشته'),
            ('this_month', 'این ماه'),
            ('last_month', 'ماه قبل'),
        )
    
    def queryset(self, request, queryset):
        today = jdatetime.date.today()
        
        if self.value() == 'today':
            start = today.togregorian()
            end = today.togregorian()
            return queryset.filter(publish_date__date=start)
        
        if self.value() == 'yesterday':
            yesterday = today - jdatetime.timedelta(days=1)
            start = yesterday.togregorian()
            return queryset.filter(publish_date__date=start)
        
        if self.value() == 'last_7_days':
            start = (today - jdatetime.timedelta(days=7)).togregorian()
            return queryset.filter(publish_date__date__gte=start)
        
        if self.value() == 'this_month':
            start = jdatetime.date(today.year, today.month, 1).togregorian()
            return queryset.filter(publish_date__date__gte=start)
        
        if self.value() == 'last_month':
            if today.month == 1:
                last_month = jdatetime.date(today.year - 1, 12, 1)
            else:
                last_month = jdatetime.date(today.year, today.month - 1, 1)
            start = last_month.togregorian()
            end = (last_month + jdatetime.timedelta(days=32)).togregorian()
            return queryset.filter(publish_date__date__gte=start, publish_date__date__lt=end)
        
        return queryset