from django.urls import path
from .views import (
    start_interview_view,
    interview_arena_view,
    get_next_question_api,
    submit_answer_api,
    report_detail_view,
    transcribe_audio_api
)

urlpatterns = [
    path('start/', start_interview_view, name='start_interview'),
    path('<uuid:session_id>/arena/', interview_arena_view, name='interview_arena'),
    path('<uuid:session_id>/report/', report_detail_view, name='interview_report'),
    
    # Asynchronous JSON APIs
    path('api/<uuid:session_id>/next-question/', get_next_question_api, name='api_next_question'),
    path('api/<uuid:session_id>/submit-answer/', submit_answer_api, name='api_submit_answer'),
    path('api/<uuid:session_id>/transcribe/', transcribe_audio_api, name='api_transcribe_audio'),
]

