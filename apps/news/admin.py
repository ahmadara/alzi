from django.contrib import admin
from .models import NewsCategory, NewsArticle, NewsComment
from unfold.admin import ModelAdmin

@admin.register(NewsCategory)
class NewsCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']


@admin.register(NewsArticle)
class NewsArticleAdmin(ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'publish_date', 'views', 'likes']
    list_filter = ['category', 'is_published', 'publish_date']
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'


@admin.register(NewsComment)
class NewsCommentAdmin(ModelAdmin):
    list_display = ['article', 'user', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['comment']
    list_editable = ['is_approved']