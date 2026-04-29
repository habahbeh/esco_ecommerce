from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.translation import get_language

from .models import BlogPost, BlogCategory, BlogTag, BlogPostFAQ

SIDEBAR_CACHE_TTL = 300


def get_sidebar_context():
    lang = get_language() or 'ar'
    cache_key = f'blog_sidebar_{lang}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    categories = list(BlogCategory.objects.filter(is_active=True).annotate(
        post_count=Count('posts', filter=Q(posts__status='published', posts__published_at__lte=timezone.now()))
    ).filter(post_count__gt=0))

    recent_posts = list(BlogPost.published().select_related('category')[:5])

    popular_tags = list(BlogTag.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).order_by('-post_count')[:15])

    ctx = {
        'blog_categories': categories,
        'recent_posts': recent_posts,
        'popular_tags': popular_tags,
    }
    cache.set(cache_key, ctx, SIDEBAR_CACHE_TTL)
    return ctx


def post_list(request):
    posts = BlogPost.published().select_related('category', 'author').prefetch_related('tags')

    q = request.GET.get('q', '').strip()
    if q:
        lang = get_language()
        if lang == 'en':
            posts = posts.filter(Q(title_en__icontains=q) | Q(content_en__icontains=q) | Q(title__icontains=q))
        else:
            posts = posts.filter(Q(title__icontains=q) | Q(content__icontains=q))

    featured_posts = BlogPost.published().filter(is_featured=True).select_related('category')[:3]

    paginator = Paginator(posts, 9)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    context = {
        'posts': posts_page,
        'featured_posts': featured_posts,
        'search_query': q,
        **get_sidebar_context(),
    }
    return render(request, 'blog/post_list.html', context)


def post_detail(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related('category', 'author').prefetch_related('tags', 'related_products', 'related_categories'),
        slug=slug,
        status='published',
        published_at__lte=timezone.now()
    )
    post.increment_views()

    if post.category:
        related_posts = BlogPost.published().filter(category=post.category).exclude(pk=post.pk).select_related('category')[:4]
    else:
        related_posts = BlogPost.published().exclude(pk=post.pk).select_related('category')[:4]

    post_faqs = post.faqs.filter(is_active=True).order_by('sort_order')

    context = {
        'post': post,
        'related_posts': related_posts,
        'post_faqs': post_faqs,
        **get_sidebar_context(),
    }
    return render(request, 'blog/post_detail.html', context)


def category_posts(request, slug):
    category = get_object_or_404(BlogCategory, slug=slug, is_active=True)
    posts = BlogPost.published().filter(category=category).select_related('category', 'author').prefetch_related('tags')

    paginator = Paginator(posts, 9)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    context = {
        'category': category,
        'posts': posts_page,
        **get_sidebar_context(),
    }
    return render(request, 'blog/category_posts.html', context)


def tag_posts(request, slug):
    tag = get_object_or_404(BlogTag, slug=slug)
    posts = BlogPost.published().filter(tags=tag).select_related('category', 'author').prefetch_related('tags')

    paginator = Paginator(posts, 9)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    context = {
        'tag': tag,
        'posts': posts_page,
        **get_sidebar_context(),
    }
    return render(request, 'blog/tag_posts.html', context)
