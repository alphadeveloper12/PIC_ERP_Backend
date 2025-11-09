from django.urls import path
from . import views

urlpatterns = [
    path('import_all/', views.import_all_data, name='import_all_data'),  # The URL for importing data
]
