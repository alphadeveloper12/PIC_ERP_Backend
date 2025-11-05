from django.urls import path, include
from .views import *

urlpatterns = [
    path('create_trip_plan/', create_trip_plan, name='create_trip_plan'),  # OpenAI API endpoints
    path('flight-schedule/', FlightDetailsAPIView.as_view(), name='flight-schedule'),

    
]