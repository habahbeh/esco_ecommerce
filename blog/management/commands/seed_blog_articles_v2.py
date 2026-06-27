"""
Seed 25 SEO-optimized bilingual blog articles for ESCO Jordan.
Reads article data from articles_data.json in the same directory.
"""
import json
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import BlogPost, BlogCategory, BlogTag, BlogPostFAQ
from accounts.models import User


class Command(BaseCommand):
    help = 'Seed 25 SEO-optimized blog articles from generated JSON data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        data_path = os.path.join(os.path.dirname(__file__), 'articles_data.json')

        with open(data_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        self.stdout.write(f'Found {len(articles)} articles to seed')

        author = User.objects.filter(is_superuser=True).first()
        if not author:
            author = User.objects.first()
        if not author:
            self.stderr.write(self.style.ERROR('No users found. Create a user first.'))
            return

        created_count = 0
        skipped_count = 0

        for i, article in enumerate(articles, 1):
            slug = article['slug']

            if BlogPost.objects.filter(slug=slug).exists():
                self.stdout.write(f'  [{i}/25] SKIP (exists): {slug}')
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f'  [{i}/25] WOULD CREATE: {slug}')
                created_count += 1
                continue

            category = None
            cat_slug = article.get('category_slug', '')
            if cat_slug:
                category = BlogCategory.objects.filter(slug=cat_slug).first()

            content_ar = article.get('content_ar', '')
            content_en = article.get('content_en', '')
            if content_ar.startswith('&lt;'):
                import html
                content_ar = html.unescape(content_ar)
                content_en = html.unescape(content_en)

            post = BlogPost.objects.create(
                title=article['title_ar'],
                title_en=article.get('title_en', ''),
                slug=slug,
                category=category,
                author=author,
                excerpt=article.get('excerpt_ar', '')[:300],
                excerpt_en=article.get('excerpt_en', '')[:300],
                content=content_ar,
                content_en=content_en,
                card_icon=article.get('card_icon', 'fa-newspaper'),
                card_icon_color=article.get('card_icon_color', '#2563eb'),
                status='published',
                is_featured=(i <= 5),
                meta_title=article.get('meta_title', '')[:200],
                meta_description=article.get('meta_description', '')[:160],
                meta_keywords=article.get('meta_keywords', '')[:200],
                published_at=timezone.now(),
            )

            tag_names = article.get('tags', [])
            for tag_name in tag_names:
                tag = BlogTag.objects.filter(name=tag_name).first()
                if tag:
                    post.tags.add(tag)

            faqs = article.get('faqs', [])
            for j, faq in enumerate(faqs):
                BlogPostFAQ.objects.create(
                    post=post,
                    question=faq.get('question_ar', ''),
                    question_en=faq.get('question_en', ''),
                    answer=faq.get('answer_ar', ''),
                    answer_en=faq.get('answer_en', ''),
                    sort_order=j,
                    is_active=True,
                )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'  [{i}/25] CREATED: {slug} ({len(faqs)} FAQs)'
            ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created: {created_count}, Skipped: {skipped_count}'
        ))
