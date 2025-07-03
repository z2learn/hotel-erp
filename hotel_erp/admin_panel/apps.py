from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    """
    Django App Configuration for Admin Panel Module
    
    This module handles:
    - Super admin functionality
    - User management for all system users
    - System-wide settings and configurations
    - Dashboard with system overview
    - Reports and analytics
    - Permanent user account creation for staff members
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_panel'
    verbose_name = 'Hotel Admin Panel'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready
        """
        try:
            # Import signals to ensure they are registered
            import admin_panel.signals
        except ImportError:
            pass
        
        # Register any custom admin configurations
        self.setup_admin_permissions()
    
    def setup_admin_permissions(self):
        """
        Set up custom permissions for admin panel functionality
        """
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # This will be called when the app is ready
        # Custom permissions can be added here if needed
        pass