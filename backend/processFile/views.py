# catalog/views.py
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UploadJob
from .tasks import process_csv_phase1
from django.views.decorators.http import require_POST
from .models import Product
import json

@csrf_exempt
def upload_products(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    upload_file = request.FILES.get('file')
    if not upload_file:
        return JsonResponse({"error": "file missing"}, status=400)

    # ensure MEDIA_ROOT exists
    tmp_dir = settings.MEDIA_ROOT
    os.makedirs(tmp_dir, exist_ok=True)
    file_name = f"{upload_file.name}-{os.urandom(6).hex()}"
    file_path = os.path.join(tmp_dir, file_name)

    # save file
    with open(file_path, 'wb') as fh:
        for chunk in upload_file.chunks():
            fh.write(chunk)

    job = UploadJob.objects.create(filename=upload_file.name, status="pending")

    # enqueue Phase 1 job to 'imports' queue
    process_csv_phase1.apply_async(args=[str(job.id), file_path], queue='imports')

    return JsonResponse({"job_id": str(job.id)}, status=202)

@csrf_exempt
@require_POST
def update_product_status(request, product_id):
    try:
        body = json.loads(request.body)
        active = body.get("active", None)
        if active is None:
            return JsonResponse({"error": "Missing 'active' field"}, status=400)

        product = Product.objects.get(id=product_id)
        product.active = active
        product.save()

        return JsonResponse({
            "id": product.id,
            "active": product.active
        })
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
# @csrf_exempt
# @require_DELETE
# def delete_product(request, product_id):
#     try:
#         product = Product.objects.get(id=product_id)
#         product.delete()
#         return JsonResponse({"status": "deleted"})
#     except Product.DoesNotExist:
#         return JsonResponse({"error": "Product not found"}, status=404)