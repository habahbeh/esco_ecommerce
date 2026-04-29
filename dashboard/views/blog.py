import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Count, Q, Sum

from blog.models import BlogPost, BlogCategory, BlogTag, BlogPostFAQ
from dashboard.forms.blog_forms import BlogPostForm, BlogCategoryForm, BlogTagForm


# ========================= Blog Posts =========================

@staff_member_required
def dashboard_blog_posts(request):
    posts = BlogPost.objects.select_related('category', 'author').order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        posts = posts.filter(status=status_filter)

    q = request.GET.get('q', '').strip()
    if q:
        posts = posts.filter(Q(title__icontains=q) | Q(title_en__icontains=q))

    agg = BlogPost.objects.aggregate(
        total=Count('id'),
        published=Count('id', filter=Q(status='published')),
        draft=Count('id', filter=Q(status='draft')),
        total_views=Sum('views_count'),
    )
    stats = {
        'total': agg['total'],
        'published': agg['published'],
        'draft': agg['draft'],
        'total_views': agg['total_views'] or 0,
    }

    context = {
        'posts': posts,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': q,
        'page_title': _('إدارة المقالات'),
        'current_page': _('المقالات'),
    }
    return render(request, 'dashboard/blog/post_list.html', context)


@staff_member_required
def dashboard_blog_post_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            if not post.author_id:
                post.author = request.user
            post.save()
            form.save_m2m()
            _save_blog_faqs(request, post)
            messages.success(request, _('تم إضافة المقال بنجاح'))
            return redirect('dashboard:dashboard_blog_posts')
    else:
        form = BlogPostForm()

    context = {
        'form': form,
        'page_title': _('إضافة مقال جديد'),
        'current_page': _('إضافة مقال جديد'),
        'faqs_json': '[]',
    }
    return render(request, 'dashboard/blog/post_form.html', context)


@staff_member_required
def dashboard_blog_post_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            _save_blog_faqs(request, post)
            messages.success(request, _('تم تحديث المقال بنجاح'))
            return redirect('dashboard:dashboard_blog_posts')
    else:
        form = BlogPostForm(instance=post)

    faqs = post.faqs.all().order_by('sort_order')
    faqs_json = json.dumps([{
        'id': faq.id,
        'question': faq.question,
        'question_en': faq.question_en,
        'answer': faq.answer,
        'answer_en': faq.answer_en,
        'sort_order': faq.sort_order,
        'is_active': faq.is_active,
    } for faq in faqs])

    context = {
        'form': form,
        'post': post,
        'page_title': _('تعديل المقال'),
        'current_page': _('تعديل المقال'),
        'faqs_json': faqs_json,
    }
    return render(request, 'dashboard/blog/post_form.html', context)


@staff_member_required
def dashboard_blog_post_delete(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        post.delete()
        messages.success(request, _('تم حذف المقال بنجاح'))
        return redirect('dashboard:dashboard_blog_posts')

    context = {
        'post': post,
        'page_title': _('حذف المقال'),
        'current_page': _('حذف المقال'),
    }
    return render(request, 'dashboard/blog/post_confirm_delete.html', context)


# ========================= Blog Categories =========================

@staff_member_required
def dashboard_blog_categories(request):
    categories = BlogCategory.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).order_by('sort_order', 'name')

    context = {
        'categories': categories,
        'page_title': _('تصنيفات المدونة'),
        'current_page': _('التصنيفات'),
    }
    return render(request, 'dashboard/blog/category_list.html', context)


@staff_member_required
def dashboard_blog_category_create(request):
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم إضافة التصنيف بنجاح'))
            return redirect('dashboard:dashboard_blog_categories')
    else:
        form = BlogCategoryForm()

    context = {
        'form': form,
        'page_title': _('إضافة تصنيف جديد'),
        'current_page': _('إضافة تصنيف'),
    }
    return render(request, 'dashboard/blog/category_form.html', context)


@staff_member_required
def dashboard_blog_category_edit(request, pk):
    category = get_object_or_404(BlogCategory, pk=pk)

    if request.method == 'POST':
        form = BlogCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث التصنيف بنجاح'))
            return redirect('dashboard:dashboard_blog_categories')
    else:
        form = BlogCategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'page_title': _('تعديل التصنيف'),
        'current_page': _('تعديل التصنيف'),
    }
    return render(request, 'dashboard/blog/category_form.html', context)


@staff_member_required
def dashboard_blog_category_delete(request, pk):
    category = get_object_or_404(BlogCategory, pk=pk)

    if request.method == 'POST':
        category.delete()
        messages.success(request, _('تم حذف التصنيف بنجاح'))
        return redirect('dashboard:dashboard_blog_categories')

    context = {
        'category': category,
        'page_title': _('حذف التصنيف'),
        'current_page': _('حذف التصنيف'),
    }
    return render(request, 'dashboard/blog/category_confirm_delete.html', context)


# ========================= Blog Tags =========================

@staff_member_required
def dashboard_blog_tags(request):
    tags = BlogTag.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).order_by('name')

    context = {
        'tags': tags,
        'page_title': _('وسوم المدونة'),
        'current_page': _('الوسوم'),
    }
    return render(request, 'dashboard/blog/tag_list.html', context)


@staff_member_required
def dashboard_blog_tag_create(request):
    if request.method == 'POST':
        form = BlogTagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم إضافة الوسم بنجاح'))
            return redirect('dashboard:dashboard_blog_tags')
    else:
        form = BlogTagForm()

    context = {
        'form': form,
        'page_title': _('إضافة وسم جديد'),
        'current_page': _('إضافة وسم'),
    }
    return render(request, 'dashboard/blog/tag_form.html', context)


@staff_member_required
def dashboard_blog_tag_edit(request, pk):
    tag = get_object_or_404(BlogTag, pk=pk)

    if request.method == 'POST':
        form = BlogTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث الوسم بنجاح'))
            return redirect('dashboard:dashboard_blog_tags')
    else:
        form = BlogTagForm(instance=tag)

    context = {
        'form': form,
        'tag': tag,
        'page_title': _('تعديل الوسم'),
        'current_page': _('تعديل الوسم'),
    }
    return render(request, 'dashboard/blog/tag_form.html', context)


@staff_member_required
def dashboard_blog_tag_delete(request, pk):
    tag = get_object_or_404(BlogTag, pk=pk)

    if request.method == 'POST':
        tag.delete()
        messages.success(request, _('تم حذف الوسم بنجاح'))
        return redirect('dashboard:dashboard_blog_tags')

    context = {
        'tag': tag,
        'page_title': _('حذف الوسم'),
        'current_page': _('حذف الوسم'),
    }
    return render(request, 'dashboard/blog/tag_confirm_delete.html', context)


def _save_blog_faqs(request, post):
    faqs_json_str = request.POST.get('blog_faqs_json', '[]')
    deleted_json_str = request.POST.get('deleted_blog_faqs_json', '[]')
    try:
        faqs_data = json.loads(faqs_json_str) if faqs_json_str.strip() else []
        deleted_ids = json.loads(deleted_json_str) if deleted_json_str.strip() else []

        if deleted_ids:
            BlogPostFAQ.objects.filter(id__in=deleted_ids, post=post).delete()

        for faq_data in faqs_data:
            question = faq_data.get('question', '').strip()
            if not question:
                continue

            faq_id = faq_data.get('id')
            defaults = {
                'question': question,
                'question_en': faq_data.get('question_en', '').strip(),
                'answer': faq_data.get('answer', '').strip(),
                'answer_en': faq_data.get('answer_en', '').strip(),
                'sort_order': faq_data.get('sort_order', 0),
                'is_active': faq_data.get('is_active', True),
            }

            if faq_id and int(faq_id) > 0:
                BlogPostFAQ.objects.filter(id=faq_id, post=post).update(**defaults)
            else:
                BlogPostFAQ.objects.create(post=post, **defaults)

    except (json.JSONDecodeError, ValueError, TypeError):
        messages.warning(request, _('حدث خطأ في معالجة بيانات الأسئلة الشائعة'))
