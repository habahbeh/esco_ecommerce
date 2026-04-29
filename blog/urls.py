from django.urls import path, re_path
from . import views

app_name = 'blog'

SLUG_RE = r'[-\w؀-ۿ]+'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    re_path(rf'category/(?P<slug>{SLUG_RE})/', views.category_posts, name='category'),
    re_path(rf'tag/(?P<slug>{SLUG_RE})/', views.tag_posts, name='tag'),
    re_path(rf'(?P<slug>{SLUG_RE})/', views.post_detail, name='post_detail'),
]
