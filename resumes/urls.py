from django.urls import path
from .views import upload_view, resume_detail_view, compare_jd_view

urlpatterns = [
    path('upload/', upload_view, name='resume_upload'),
    path('<uuid:resume_id>/', resume_detail_view, name='resume_detail'),
    path('<uuid:resume_id>/compare-jd/', compare_jd_view, name='compare_jd'),
]
