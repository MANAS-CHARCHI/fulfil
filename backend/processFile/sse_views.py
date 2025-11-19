# catalog/sse_views.py
import asyncio
import json
from django.http import StreamingHttpResponse
from django.core.paginator import Paginator
from .models import Product
from .redis_utils import get_progress
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

async def _async_sleep(seconds):
    await asyncio.sleep(seconds)

def progress_stream(request, job_id):

    async def event_generator():
        last = None

        while True:
            data = get_progress(job_id)
            payload = {
                "status": data.get("status", "pending"),
                "processed": int(data.get("processed") or 0),
                "total": int(data.get("total") or 0),
                "error": data.get("error"),
            }

            if payload != last:
                yield f"data: {json.dumps(payload)}\n\n"
                last = payload

            if payload["status"] in ("completed", "failed"):
                # send final event so EventSource can close
                yield "data: [DONE]\n\n"
                return   # <-- IMPORTANT: ends generator cleanly

            await _async_sleep(0.5)

    async def wrapper():
        async for chunk in event_generator():
            yield chunk.encode("utf-8")

    response = StreamingHttpResponse(wrapper(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # for nginx
    return response

@require_GET
@csrf_exempt
def stream_devices(request):
    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 100))
    sku_filter = request.GET.get("sku", None)
    active_filter = request.GET.get("active", None)

    qs = Product.objects.all()

    if sku_filter:
        qs = qs.filter(sku__icontains=sku_filter)

    if active_filter is not None:
        if active_filter.lower() == "true":
            qs = qs.filter(active=True)
        elif active_filter.lower() == "false":
            qs = qs.filter(active=False)
    total_count = qs.count()
    paginator = Paginator(qs, limit)
    page_obj = paginator.get_page(page)
    

    def stream():
        for device in page_obj.object_list:
            data = {
                "id": device.id,
                "sku": device.sku,
                "name": device.name,
                "description": device.description,
                "active": device.active,
                "created_at": device.created_at.isoformat(),
                "updated_at": device.updated_at.isoformat(),
            }
            yield json.dumps(data) + "\n"

    response = StreamingHttpResponse(stream(), content_type="application/json")
    response["X-Total-Count"] = str(total_count)
    # Expose header for JS
    response["Access-Control-Expose-Headers"] = "X-Total-Count"
    return response