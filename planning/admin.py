from django.contrib import admin

from rl_engine.rl_feedback_loop import RLFeedbackHandler
from .models import *
# Register your models here.

admin.site.register(PrimaveraSheet)
admin.site.register(P6Activity)
admin.site.register(MappingResult)