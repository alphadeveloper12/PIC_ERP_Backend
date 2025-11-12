from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(Schedule)
admin.site.register(WorkBreakdownItem)
admin.site.register(Task)
admin.site.register(TaskDependency)
admin.site.register(Resource)
admin.site.register(Assignment)
admin.site.register(XerImportJob)