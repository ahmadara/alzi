from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import NewsArticle, NewsCategory

class NewsListView(ListView):
    model = NewsArticle
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 10
    
    def get_queryset(self):
        return NewsArticle.objects.filter(is_published=True).order_by('-publish_date')


class NewsDetailView(DetailView):
    model = NewsArticle
    template_name = 'news/news_detail.html'
    context_object_name = 'news'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views += 1
        obj.save()
        return obj


class CategoryView(ListView):
    model = NewsArticle
    template_name = 'news/category_list.html'
    context_object_name = 'news_list'
    paginate_by = 10
    
    def get_queryset(self):
        self.category = get_object_or_404(NewsCategory, slug=self.kwargs['slug'])
        return NewsArticle.objects.filter(category=self.category, is_published=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
    