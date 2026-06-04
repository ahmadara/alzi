from django.contrib import admin
from unfold.admin import ModelAdmin
import jdatetime
from .filters import JalaliDateRangeFilter
from .models import NewsCategory, NewsArticle, NewsComment

@admin.register(NewsCategory)
class NewsCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']


@admin.register(NewsArticle)
class NewsArticleAdmin(ModelAdmin):
    list_display = ['title', 'category', 'jalali_publish_date', 'views', 'likes', 'is_published']
    list_filter = [
        'category',
        'is_published',
        JalaliDateRangeFilter,  # فیلتر تاریخ بازه‌ای (بدون پرانتز)
    ]
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    
    @admin.display(description="تاریخ انتشار (شمسی)")
    def jalali_publish_date(self, obj):
        """نمایش تاریخ شمسی در لیست"""
        jd = jdatetime.date.fromgregorian(date=obj.publish_date)
        return jd.strftime("%Y/%m/%d")
    
    @admin.display(description="تاریخ انتشار (میلادی)")
    def publish_date_miladi(self, obj):
        return obj.publish_date.strftime("%Y/%m/%d %H:%M")


@admin.register(NewsComment)
class NewsCommentAdmin(ModelAdmin):
    list_display = ['article', 'user', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['comment']
    list_editable = ['is_approved']