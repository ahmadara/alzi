from django.urls import path
from .views import NewsListView, NewsDetailView, CategoryView

app_name = "news"

urlpatterns = [
    path("", NewsListView.as_view(), name="list"),
    path("<slug:slug>/", NewsDetailView.as_view(), name="detail"),
    path("category/<slug:slug>/", CategoryView.as_view(), name="category"),
]
