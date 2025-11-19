# catalog/tasks.py
import csv
import io
from celery import shared_task, Task
from django.db import connection
from .models import UploadJob
from .redis_utils import set_progress

BATCH = 2000


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 5}
    retry_backoff = True


# ---------------------------------------------------------
# PHASE 1 — PARSING CSV + STAGING INSERT
# ---------------------------------------------------------
@shared_task(bind=True, base=BaseTaskWithRetry)
def process_csv_phase1(self, job_id, file_path):
    job = UploadJob.objects.get(id=job_id)

    # ❗ Start parsing phase
    job.status = "parsing"
    job.save(update_fields=["status"])
    set_progress(job_id, processed=0, total=0, status="parsing")

    rows = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)

            # Prepare temp CSV
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(["job_id"] + header)

            # 🔥 PARSING PROGRESS (real-time)
            for row in reader:
                writer.writerow([job_id] + row)
                rows += 1

                if rows % 5000 == 0:
                    set_progress(job_id, processed=rows, total=rows, status="parsing")

            out.seek(0)

            # Switch status to staging
            job.status = "staging"
            job.save(update_fields=["status"])

            copy_sql = f"""
                COPY product_import_staging (job_id, {", ".join(header)})
                FROM STDIN WITH CSV HEADER
            """

            # Perform COPY
            with connection.cursor() as cur:
                cur.copy_expert(copy_sql, out)

        # Finish phase
        job.total_rows = rows
        job.processed_rows = rows
        job.save(update_fields=["total_rows", "processed_rows"])

        # 🔥 FINISHED STAGING
        set_progress(job_id, processed=rows, total=rows, status="staging")

    except Exception as exc:
        err_msg = str(exc)
        job.status = "failed"
        job.error_message = err_msg
        job.save(update_fields=["status", "error_message"])
        set_progress(job_id, status="failed", error=err_msg)
        raise

    # ---------------------------------------------------------
    # Move to PHASE 2
    # ---------------------------------------------------------
    from .tasks import process_csv_phase2
    process_csv_phase2.apply_async(args=[job_id], queue="imports_merge")


# ---------------------------------------------------------
# PHASE 2 — MERGE INTO MAIN TABLE
# ---------------------------------------------------------
@shared_task(bind=True, base=BaseTaskWithRetry)
def process_csv_phase2(self, job_id):
    job = UploadJob.objects.get(id=job_id)

    # 🔥 Start importing phase
    job.status = "importing"
    job.save(update_fields=["status"])
    set_progress(job_id, status="importing", processed=0, total=1)

    try:
        with connection.cursor() as cur:
            merge_sql = """
                INSERT INTO "processFile_product"
                (sku, name, description, active, created_at, updated_at)
                SELECT DISTINCT ON (LOWER(sku))
                    LOWER(sku), name, description, TRUE, now(), now()
                FROM product_import_staging
                WHERE job_id = %s
                ORDER BY LOWER(sku), id DESC
                ON CONFLICT (sku) DO UPDATE SET
                    name=EXCLUDED.name,
                    description=EXCLUDED.description,
                    active=EXCLUDED.active,
                    updated_at=now();
            """
            cur.execute(merge_sql, [job_id])

        # 🔥 100% importing done
        set_progress(job_id, processed=1, total=1, status="importing")

        # Cleanup staging
        with connection.cursor() as cur:
            cur.execute("DELETE FROM product_import_staging WHERE job_id = %s", [job_id])

        # Completed
        job.status = "completed"
        job.processed_rows = job.total_rows
        job.save(update_fields=["status", "processed_rows"])

        # Final SSE push
        set_progress(job_id, processed=job.total_rows, total=job.total_rows, status="completed")

    except Exception as exc:
        err_msg = str(exc)
        job.status = "failed"
        job.error_message = err_msg
        job.save(update_fields=["status", "error_message"])
        set_progress(job_id, status="failed", error=err_msg)
        raise
