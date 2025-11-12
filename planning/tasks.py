from celery import shared_task
from django.utils import timezone
from .models import XerImportJob
from .importer import XerImporter


@shared_task(bind=True)
def import_xer_background(self, job_id):
    try:
        job = XerImportJob.objects.get(id=job_id)
        job.status = 'processing'
        job.save(update_fields=['status'])

        importer = XerImporter()
        with open(job.file.path, 'rb') as f:
            parsed = importer.parse_xer(f)
        summary = importer.import_data(parsed, job.planning)

        job.status = 'completed'
        job.completed_at = timezone.now()
        job.summary = summary
        job.message = "✅ Import completed successfully"
        job.save(update_fields=['status', 'completed_at', 'summary', 'message'])

    except Exception as e:
        job.status = 'failed'
        job.message = str(e)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'completed_at', 'message'])
        raise
