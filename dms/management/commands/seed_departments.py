from django.core.management.base import BaseCommand
from dms.models import Department

class Command(BaseCommand):
    help = 'Seeds production departments'

    def handle(self, *args, **kwargs):
        departments = [
            {'name': 'Engineering', 'code': 'ENG'},
            {'name': 'Procurement', 'code': 'PROC'},
            {'name': 'Construction', 'code': 'CONST'},
            {'name': 'Project Management', 'code': 'PJM'},
            {'name': 'Quality Control', 'code': 'QC'},
            {'name': 'Health, Safety & Environment', 'code': 'HSE'},
            {'name': 'Finance', 'code': 'FIN'},
            {'name': 'Human Resources', 'code': 'HR'},
            {'name': 'Information Technology', 'code': 'IT'},
        ]

        for dep_data in departments:
            dep, created = Department.objects.get_or_create(
                code=dep_data['code'],
                defaults={'name': dep_data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created department: {dep.name}"))
            else:
                self.stdout.write(f"Department exists: {dep.name}")
