from django.contrib import admin

from rl_engine_v2.rl_feedback_v2 import RLFeedbackHandler
from .models import *
# Register your models here.

admin.site.register(PrimaveraSheet)
admin.site.register(P6Activity)
admin.site.register(MappingResult)