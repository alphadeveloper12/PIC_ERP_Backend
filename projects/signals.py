# models.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import models
from projects.models import Project


@receiver(pre_save, sender=Project)
def set_project_code(sender, instance, **kwargs):
    if not instance.code:  # Only generate if code is empty
        prefix = "PRJ-"
        last_project = Project.objects.filter(company=instance.company).order_by('id').last()
        if last_project:
            last_id = int(last_project.code.split('-')[-1])
            new_id = last_id + 1
        else:
            new_id = 1
        instance.code = f"{prefix}{new_id:04d}"