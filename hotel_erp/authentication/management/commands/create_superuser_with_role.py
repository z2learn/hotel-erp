from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with admin role'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username for the superuser')
        parser.add_argument('--email', required=True, help='Email for the superuser')
        parser.add_argument('--password', required=True, help='Password for the superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists')

        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email "{email}" already exists')

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='admin'
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser "{username}" with admin role')
        )