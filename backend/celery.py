# backend/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from pathlib import Path

# Tell Celery where Django settings are located
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Create the Celery app instance
app = Celery('backend')

# Load configuration from Django settings, prefixing all celery-related keys with "CELERY_"
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks across all registered Django apps
# Celery will look for a file named "tasks.py" in each app
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

@app.on_after_configure.connect
def cleanup_old_messages(sender, **kwargs):
    base_path = Path(__file__).resolve().parent.parent / "celery"
    for folder in ["in", "out", "processed"]:
        path = base_path / folder
        if path.exists():
            for f in path.glob("*.msg"):
                try:
                    f.unlink()
                except Exception:
                    pass