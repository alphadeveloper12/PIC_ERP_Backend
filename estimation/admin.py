from django.contrib import admin
from .models import *

admin.site.register(Estimation)
admin.site.register(BOQ)
admin.site.register(Section)
admin.site.register(Subsection)
admin.site.register(BOQItem)
admin.site.register(BOQRevision)
