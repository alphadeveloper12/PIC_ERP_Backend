from celery import shared_task
from .models import Document, Task
from django.utils import timezone
import time

@shared_task
def process_document_ai(document_id):
    """
    Simulates AI processing: OCR extraction and Summarization.
    """
    try:
        doc = Document.objects.get(id=document_id)
        doc.embedding_status = 'PENDING'
        doc.save()
        
        # Simulate Processing Delay
        time.sleep(2)
        
        # Placeholder for actual AI Logic (e.g. Call OpenAI, Tesseract)
        # For now, just dummy text
        doc.extracted_text = f"Extracted text content from {doc.file.name}..."
        doc.ai_summary = f"Auto-generated summary for {doc.document_type}."
        doc.embedding_status = 'PROCESSED'
        doc.save()
        
        return f"Document {document_id} processed successfully."
        
    except Document.DoesNotExist:
        return f"Document {document_id} not found."
    except Exception as e:
        if 'doc' in locals():
            doc.embedding_status = 'FAILED'
            doc.save()
        return f"Error processing document {document_id}: {str(e)}"

@shared_task
def check_sla_breaches():
    """
    Periodic task to check for overdue tasks.
    """
    now = timezone.now()
    overdue_tasks = Task.objects.filter(
        status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS'],
        due_date__lt=now
    )
    
    count = 0
    for task in overdue_tasks:
        # Send Notification (Placeholder)
        print(f"SLA Breach detected for Task {task.id}: {task}")
        count += 1
        
    return f"Checked SLA. Found {count} breaches."
