from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Rebuild Meilisearch index for all products'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear index before rebuilding')
        parser.add_argument('--setup', action='store_true', help='Configure index settings (searchable/filterable attributes, synonyms)')
        parser.add_argument('--batch-size', type=int, default=500, help='Batch size for indexing (default: 500)')

    def handle(self, *args, **options):
        from products.search.client import is_available
        from products.search.indexer import MeilisearchIndexer

        if not is_available():
            self.stderr.write(self.style.ERROR('Meilisearch is not available. Check your connection settings.'))
            return

        indexer = MeilisearchIndexer()

        if options['clear']:
            self.stdout.write('Clearing index...')
            indexer.clear_index()
            self.stdout.write(self.style.SUCCESS('Index cleared.'))

        if options['setup']:
            self.stdout.write('Configuring index settings...')
            if indexer.setup_index():
                self.stdout.write(self.style.SUCCESS('Index configured.'))
            else:
                self.stderr.write(self.style.ERROR('Failed to configure index.'))
                return

        self.stdout.write('Indexing all products...')
        total = indexer.index_all_products(batch_size=options['batch_size'])
        self.stdout.write(self.style.SUCCESS(f'Successfully indexed {total} products.'))
