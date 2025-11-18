import os, uuid
from django.http import StreamingHttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
from django_redis import get_redis_connection
from .tasks import split_csv_into_chunks

UPLOAD_DIR = settings.MEDIA_ROOT

@api_view(["POST"])
def upload_csv(request):
    f = request.FILES["file"]

    uid = uuid.uuid4().hex
    path = os.path.join(UPLOAD_DIR, f"{uid}.csv")

    with open(path, "wb+") as d:
        for chunk in f.chunks():
            d.write(chunk)

    task = split_csv_into_chunks.apply_async(args=[path], queue="upload")

    return Response({"task_id": task.id})


# SSE EVENT STREAM
def event_stream(task_id):
    r = get_redis_connection("default")
    pub = r.pubsub()
    pub.subscribe(f"progress_{task_id}")

    for msg in pub.listen():
        if msg["type"] != "message":
            continue
        yield f"data: {msg['data'].decode()}\n\n"


def progress_sse(request, task_id):
    resp = StreamingHttpResponse(event_stream(task_id),
                                 content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp
