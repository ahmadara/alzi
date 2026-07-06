from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
import jdatetime
from .filters import JalaliDateRangeFilter
from .models import NewsCategory, NewsArticle, NewsComment


@admin.register(NewsCategory)
class NewsCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'order', 'display_is_active', 'get_article_count']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']
    search_fields = ['name']
    ordering = ['order', 'name']

    fieldsets = (
        ('اطلاعات دسته‌بندی', {
            'fields': ('name', 'slug', 'icon', 'order', 'is_active')
        }),
        ('تصویر پیش‌فرض', {
            'fields': ('default_image',)
        }),
    )

    @display(boolean=True, description="فعال")
    def display_is_active(self, obj):
        return obj.is_active

    @display(description="تعداد مقالات")
    def get_article_count(self, obj):
        return obj.news.count()


@admin.register(NewsArticle)
class NewsArticleAdmin(ModelAdmin):
    list_display = [
        'title', 'category', 'display_is_published',
        'jalali_publish_date_display', 'author', 'views', 'likes'
    ]
    list_filter = ['is_published', 'category', JalaliDateRangeFilter]
    search_fields = ['title', 'summary', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    readonly_fields = ['views', 'likes', 'created_at', 'updated_at', 'jalali_publish_date_display']
    ordering = ['-publish_date']
    list_per_page = 25
    actions = ['publish_selected', 'unpublish_selected']

    fieldsets = (
        ('محتوای مقاله', {
            'fields': ('title', 'slug', 'category', 'summary', 'content')
        }),
        ('رسانه', {
            'fields': ('featured_image', 'video_url'),
            'description': 'تصویر شاخص و لینک ویدیو (اختیاری)'
        }),
        ('انتشار', {
            'fields': ('is_published', 'publish_date', 'author')
        }),
        ('آمار (فقط نمایش)', {
            'fields': ('views', 'likes', 'jalali_publish_date_display', 'created_at', 'updated_at'),
            'classes': ['collapse'],
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @display(
        label={"منتشر شده": "success", "پیش‌نویس": "warning"},
        description="وضعیت"
    )
    def display_is_published(self, obj):
        return "منتشر شده" if obj.is_published else "پیش‌نویس"

    @display(description="تاریخ انتشار (شمسی)", ordering="publish_date")
    def jalali_publish_date_display(self, obj):
        jd = jdatetime.date.fromgregorian(date=obj.publish_date)
        return jd.strftime("%Y/%m/%d")

    @admin.action(description="انتشار مقالات انتخاب‌شده")
    def publish_selected(self, request, queryset):
        count = queryset.update(is_published=True)
        self.message_user(request, f"{count} مقاله منتشر شد.")

    @admin.action(description="تبدیل به پیش‌نویس")
    def unpublish_selected(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(request, f"{count} مقاله به پیش‌نویس تبدیل شد.")


@admin.register(NewsComment)
class NewsCommentAdmin(ModelAdmin):
    list_display = [
        'get_article_title', 'user', 'get_comment_preview',
        'display_is_approved', 'created_at'
    ]
    list_filter = ['is_approved', 'created_at']
    search_fields = ['comment', 'user__username', 'user__first_name', 'article__title']
    readonly_fields = ['created_at', 'article', 'user', 'comment']
    ordering = ['-created_at']
    list_per_page = 30
    actions = ['approve_comments', 'reject_comments']

    fieldsets = (
        ('نظر', {
            'fields': ('article', 'user', 'comment', 'created_at')
        }),
        ('وضعیت', {
            'fields': ('is_approved',)
        }),
    )

    @display(description="مقاله")
    def get_article_title(self, obj):
        return obj.article.title

    @display(description="پیش‌نمایش نظر")
    def get_comment_preview(self, obj):
        return obj.comment[:70] + "…" if len(obj.comment) > 70 else obj.comment

    @display(boolean=True, description="تایید شده")
    def display_is_approved(self, obj):
        return obj.is_approved

    @admin.action(description="تایید نظرات انتخاب‌شده")
    def approve_comments(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f"{count} نظر تایید شد.")

    @admin.action(description="رد نظرات انتخاب‌شده")
    def reject_comments(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f"{count} نظر رد شد.")
