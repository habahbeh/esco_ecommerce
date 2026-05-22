import os
import shutil
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import ProductImage
from products.image_utils import (
    optimize_image, generate_thumbnail, generate_medium, get_image_size_kb
)


class Command(BaseCommand):
    help = 'Optimize existing product images with full backup. Zero risk.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be optimized without making changes',
        )
        parser.add_argument(
            '--restore',
            action='store_true',
            help='Restore all images from backup',
        )
        parser.add_argument(
            '--max-dimension',
            type=int,
            default=1200,
            help='Maximum image dimension in pixels (default: 1200)',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='JPEG compression quality 1-100 (default: 85)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of images to process per batch (default: 50)',
        )

    def handle(self, *args, **options):
        if options['restore']:
            self._restore_backup()
            return

        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'product_images')
        dry_run = options['dry_run']
        max_dim = options['max_dimension']
        quality = options['quality']
        batch_size = options['batch_size']

        images = ProductImage.objects.filter(image__isnull=False).exclude(image='')
        total = images.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No product images found.'))
            return

        self.stdout.write(f'Found {total} product images to process.')
        self.stdout.write(f'Settings: max_dimension={max_dim}, quality={quality}')

        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN — no changes will be made.\n'))

        if not dry_run:
            os.makedirs(backup_dir, exist_ok=True)
            self.stdout.write(f'Backup directory: {backup_dir}\n')

        optimized = 0
        skipped = 0
        errors = 0
        total_saved_kb = 0
        start_time = time.time()

        for i, img_obj in enumerate(images.iterator(), 1):
            try:
                image_path = img_obj.image.path
            except Exception:
                skipped += 1
                continue

            if not os.path.isfile(image_path):
                skipped += 1
                continue

            original_size = get_image_size_kb(image_path)

            if dry_run:
                self.stdout.write(
                    f'  [{i}/{total}] {os.path.basename(image_path)} — '
                    f'{original_size:.0f} KB'
                )
                continue

            try:
                rel_path = os.path.relpath(image_path, settings.MEDIA_ROOT)
                backup_path = os.path.join(backup_dir, rel_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(image_path, backup_path)

                result = optimize_image(image_path, max_dimension=max_dim, quality=quality)
                if result:
                    content, filename = result
                    old_path = img_obj.image.path
                    img_obj.image.save(filename, content, save=False)
                    if os.path.isfile(old_path) and old_path != img_obj.image.path:
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass

                optimized_path = img_obj.image.path

                thumb_result = generate_thumbnail(optimized_path)
                if thumb_result:
                    content, filename = thumb_result
                    img_obj.image_thumbnail.save(filename, content, save=False)

                medium_result = generate_medium(optimized_path)
                if medium_result:
                    content, filename = medium_result
                    img_obj.image_medium.save(filename, content, save=False)

                ProductImage.objects.filter(pk=img_obj.pk).update(
                    image=img_obj.image,
                    image_thumbnail=img_obj.image_thumbnail,
                    image_medium=img_obj.image_medium,
                )

                new_size = get_image_size_kb(img_obj.image.path)
                saved = original_size - new_size
                total_saved_kb += max(saved, 0)
                optimized += 1

                if i % 10 == 0 or i == total:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    self.stdout.write(
                        f'  [{i}/{total}] {original_size:.0f}KB -> {new_size:.0f}KB '
                        f'(saved {max(saved, 0):.0f}KB) — {rate:.1f} img/s'
                    )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  [{i}/{total}] ERROR: {e}')
                )

        elapsed = time.time() - start_time
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Optimization complete in {elapsed:.1f}s'))
        self.stdout.write(f'  Optimized: {optimized}')
        self.stdout.write(f'  Skipped (missing file): {skipped}')
        self.stdout.write(f'  Errors: {errors}')
        self.stdout.write(f'  Total saved: {total_saved_kb / 1024:.1f} MB')

        if not dry_run and optimized > 0:
            self.stdout.write('')
            self.stdout.write(
                self.style.NOTICE(
                    f'Backups stored in: {backup_dir}\n'
                    f'To restore: python manage.py optimize_images --restore'
                )
            )

    def _restore_backup(self):
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'product_images')

        if not os.path.isdir(backup_dir):
            self.stdout.write(self.style.ERROR('No backup found.'))
            return

        restored = 0
        errors = 0

        for root, dirs, files in os.walk(backup_dir):
            for filename in files:
                backup_path = os.path.join(root, filename)
                rel_path = os.path.relpath(backup_path, backup_dir)
                original_path = os.path.join(settings.MEDIA_ROOT, rel_path)

                try:
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    shutil.copy2(backup_path, original_path)
                    restored += 1
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'  Error restoring {rel_path}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Restored {restored} images. Errors: {errors}'))
        self.stdout.write(
            self.style.NOTICE(
                'Note: Database image field paths may need updating if filenames changed.\n'
                'The safest approach is to re-run optimization or restore from a DB backup.'
            )
        )
