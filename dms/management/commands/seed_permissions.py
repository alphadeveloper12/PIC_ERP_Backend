from django.core.management.base import BaseCommand
from dms.utils import seed_global_templates, initialize_project_permissions
from projects.models import Project

class Command(BaseCommand):
    help = 'Seeds global permission templates and initializes permissions for all projects'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding global templates...")
        global_count = seed_global_templates()
        self.stdout.write(self.style.SUCCESS(f"Created {global_count} global templates."))

        self.stdout.write("Initializing permissions for existing projects...")
        projects = Project.objects.all()
        total_initialized = 0
        for project in projects:
            count = initialize_project_permissions(project)
            if count > 0:
                self.stdout.write(f"Initialized {count} permissions for project: {project.name}")
                total_initialized += count
        
        self.stdout.write(self.style.SUCCESS(f"Finished! Total project-specific permissions created: {total_initialized}"))
