from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import NewsArticle, NewsCategory, NewsComment

class NewsListView(ListView):
    model = NewsArticle
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 9  # تغییر به 9 برای هماهنگی با گرید 3 ستونی
    
    def get_queryset(self):
        return NewsArticle.objects.filter(is_published=True).order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 4 خبر اول برای بخش ویژه (featured posts)
        context['featured_news'] = NewsArticle.objects.filter(is_published=True)[:4]
        # همه دسته‌بندی‌ها برای فیلتر
        context['categories'] = NewsCategory.objects.filter(is_active=True)
        return context



class NewsDetailView(DetailView):
    model = NewsArticle
    template_name = 'news/news_detail.html'
    context_object_name = 'news'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views += 1
        obj.save()
        return obj
    
    def post(self, request, *args, **kwargs):
        """پردازش فرم ثبت نظر"""
        self.object = self.get_object()
        comment_text = request.POST.get('comment')
        if comment_text and request.user.is_authenticated:
            NewsComment.objects.create(
                article=self.object,
                user=request.user,
                comment=comment_text,
                is_approved=True
            )
        return redirect('news:detail', slug=self.object.slug)



class CategoryView(ListView):
    model = NewsArticle
    template_name = 'news/category_list.html'
    context_object_name = 'news_list'
    paginate_by = 9
    
    def get_queryset(self):
        self.category = get_object_or_404(NewsCategory, slug=self.kwargs['slug'])
        return NewsArticle.objects.filter(category=self.category, is_published=True).order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = NewsCategory.objects.filter(is_active=True)
        return context
    
    