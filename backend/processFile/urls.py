from django.urls import path
from .views import upload_csv, progress_sse

urlpatterns = [
    path("upload/", upload_csv),
    path('progress/<str:task_id>/', progress_sse, name='progress_sse'),
]
