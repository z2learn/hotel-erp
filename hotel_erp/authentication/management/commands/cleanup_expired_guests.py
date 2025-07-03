from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomUser

class Command(BaseCommand):
    help = 'Clean up expired guest accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        expired_guests = CustomUser.objects.filter(
            is_temporary=True,
            expires_at__lt=timezone.now()
        )
        
        count = expired_guests.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'Would delete {count} expired guest accounts')
            )
            for guest in expired_guests:
                self.stdout.write(f'  - {guest.username} (expired: {guest.expires_at})')
        else:
            expired_guests.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} expired guest accounts')
            )