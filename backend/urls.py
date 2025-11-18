from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/auth/', include('auth_app.urls')),  # our login API
    # path('api/', include('chatgpt.urls')),  # OpenAI API endpoints
    # path('api/excel/', include('excel.urls')),  # Excel/Bill of Quantities endpoints
    # path('api/excel/', include('excel.urls')),  # Excel/Bill of Quantities endpoints
    path('api/planning/', include('planning.urls')),  # Excel/Bill of Quantities endpoints
    path('api/', include('api.urls')),  # Excel/Bill of Quantities endpoints
]
