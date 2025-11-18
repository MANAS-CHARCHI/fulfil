import csv, os
from celery import shared_task, group, chord
from .utils_csv import split_csv
from django.db import OperationalError
from .models import Product
from .progress import publish_progress
from django.conf import settings
from django.db import connection
from django.utils import timezone

# -------------------------
# STEP 1 — SPLIT CSV
# -------------------------
@shared_task(bind=True)
def split_csv_into_chunks(self, path):
    print("CELERY MEDIA_ROOT =", settings.MEDIA_ROOT)

    publish_progress(self.request.id, {"stage": "splitting"})

    chunks, folder = split_csv(path)

    publish_progress(self.request.id, {
        "stage": "chunks_created",
        "folder": folder,
        "chunks": len(chunks)
    })

    # send all chunks to "process_chunk" workers
    job = group(process_chunk.s(chunk_path) for chunk_path in chunks)

    return chord(job)(finalize_import.s(folder))


# -------------------------
# STEP 2 — PROCESS EACH CHUNK
# -------------------------
@shared_task(queue="process")
def process_chunk(chunk_path):
    print("Processing:", chunk_path)

    rows_dict = {}  # use dict to deduplicate by SKU
    now = timezone.now()

    # Read CSV and deduplicate by SKU (case-insensitive)
    with open(chunk_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row["sku"].lower()
            rows_dict[sku] = (
                sku,
                row.get("name", "")[:255],
                row.get("description", ""),
                True,  # active
                now,   # created_at
                now,   # updated_at
            )

    rows = list(rows_dict.values())

    if not rows:
        return {"processed": 0}

    # Build placeholder list for bulk insert
    placeholders = ",".join(["(%s, %s, %s, %s, %s, %s)"] * len(rows))

    # Flatten params for psycopg2
    flat_params = [value for row in rows for value in row]

    query = f"""
        INSERT INTO "processFile_product" (sku, name, description, active, created_at, updated_at)
        VALUES {placeholders}
        ON CONFLICT (sku)
        DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            active = EXCLUDED.active,
            updated_at = EXCLUDED.updated_at;
    """

    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(query, flat_params)

    return {"processed": len(rows)}


# -------------------------
# STEP 3 — FINALIZE
# -------------------------
@shared_task
def finalize_import(results, folder):
    total = sum(r["processed"] for r in results)
    publish_progress("global", {
        "stage": "completed",
        "processed": total,
        "folder": folder
    })
    return {"total": total}
