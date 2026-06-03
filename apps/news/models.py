from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

class NewsCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(unique=True, verbose_name="نامک")
    icon = models.CharField(max_length=50, blank=True, verbose_name="آیکون", help_text="کلاس FontAwesome مثل fa-news")
    order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    default_image = models.ImageField(
        upload_to='category_images/', 
        blank=True, 
        null=True, 
        verbose_name="تصویر پیش‌فرض دسته"
    )
    
    
class NewsArticle(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان")
    slug = models.SlugField(unique=True, verbose_name="نامک")
    category = models.ForeignKey(NewsCategory, on_delete=models.CASCADE, related_name='news', verbose_name="دسته‌بندی")
    
    summary = models.TextField(verbose_name="خلاصه", help_text="توضیح کوتاه برای صفحه اصلی (حداکثر 200 کاراکتر)")
    content = models.TextField(verbose_name="متن کامل")
    featured_image = models.ImageField(upload_to='news/%Y/%m/', verbose_name="تصویر شاخص")
    
    video_url = models.URLField(blank=True, null=True, verbose_name="لینک ویدیو", help_text="لینک یوتیوب یا آپارات")
    
    is_published = models.BooleanField(default=True, verbose_name="منتشر شود؟")
    publish_date = models.DateTimeField(default=timezone.now, verbose_name="تاریخ انتشار")
    
    views = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    likes = models.PositiveIntegerField(default=0, verbose_name="لایک‌ها")
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="نویسنده")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-publish_date']
        verbose_name = "خبر"
        verbose_name_plural = "اخبار"
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('news:detail', args=[self.slug])
 
    def get_image_url(self):
        """دریافت آدرس تصویر خبر (تصویر خود خبر یا پیش‌فرض دسته)"""
        if self.featured_image:
            return self.featured_image.url
        elif self.category.default_image:
            return self.category.default_image.url
        else:
            return "/static/images/placeholder-image.jpg"

class NewsComment(models.Model):
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='comments', verbose_name="خبر")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    comment = models.TextField(verbose_name="نظر")
    is_approved = models.BooleanField(default=False, verbose_name="تایید شده؟")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
    
    def __str__(self):
        return f"نظر {self.user.username} برای {self.article.title}"