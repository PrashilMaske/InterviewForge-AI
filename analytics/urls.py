from django.urls import path
from .views import dashboard_analytics_api

urlpatterns = [
    path('api/dashboard/', dashboard_analytics_api, name='api_dashboard_analytics'),
]
