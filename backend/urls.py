from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path('api/auth/', include('auth_app.urls')),  # our login API
    # path('api/excel/', include('excel.urls')),  # Excel/Bill of Quantities endpoints
    path('planning/', include('planning.urls')),  # Excel/Bill of Quantities endpoints
    path('api/', include('api.urls')),  # Excel/Bill of Quantities endpoints
    path("core/", include("core.urls", namespace="core")),
    path('api/projects/', include('projects.urls')),
    path('dms/', include('dms.urls')),
    path('contracts/', include('contracts.urls')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
