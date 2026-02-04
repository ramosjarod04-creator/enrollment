import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enrollment_system.settings')

application = get_wsgi_application()

# This is the "handler" Vercel is looking for
app = application
