import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enrollment_system.settings')

application = get_wsgi_application()

# ADD THESE LINES AT THE BOTTOM
from django.core.management import call_command
try:
    print("Attempting to run migrations...")
    call_command('migrate', interactive=False)
    print("Migrations successful!")
except Exception as e:
    print(f"Migration failed: {e}")
