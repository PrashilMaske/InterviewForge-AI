from django.urls import path
from .views import index_view, register_view, login_view, logout_view, dashboard_view, voice_test_view, live_captioning_view

urlpatterns = [
    path('', index_view, name='index'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('voice-test/', voice_test_view, name='voice_test'),
    path('live-captioning/', live_captioning_view, name='live_captioning'),
]

