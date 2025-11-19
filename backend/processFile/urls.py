from django.urls import path
from .views import upload_products, update_product_status
from .sse_views import progress_stream, stream_devices  

urlpatterns = [
    path("upload/", upload_products),
    path('progress/<str:job_id>/', progress_stream, name='progress_stream'),
    path('devices/stream/', stream_devices, name='stream_devices'),
    path('device/<int:product_id>/update-status/', update_product_status, name='update_product_status'),
]
