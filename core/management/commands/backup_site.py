from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from core.backup import create_backup, verify_backup


class Command(BaseCommand):
    help = 'Полная копия БД и media с SHA-256; хранение минимум семи копий.'

    def add_arguments(self, parser):
        parser.add_argument('--root', help='Отдельное смонтированное хранилище копий.')
        parser.add_argument('--keep', type=int, default=7)
        parser.add_argument('--verify', help='Проверить готовую копию без восстановления.')

    def handle(self, *args, **options):
        if options['verify']:
            verify_backup(options['verify'])
            self.stdout.write('Контрольные суммы и структура копии проверены.')
            return
        root = options['root'] or getattr(settings, 'BACKUP_ROOT', '')
        if not root:
            raise CommandError('Задайте BACKUP_ROOT на отдельном защищённом хранилище и ежедневный планировщик.')
        folder = create_backup(root, options['keep'])
        self.stdout.write(self.style.SUCCESS(f'Полная копия готова: {folder.name}'))
