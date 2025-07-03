from django.apps import AppConfig

class GuestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'guest'
    verbose_name = 'Guest Management'
    
    def ready(self):
        import guest.signals  # Import signals when app is ready