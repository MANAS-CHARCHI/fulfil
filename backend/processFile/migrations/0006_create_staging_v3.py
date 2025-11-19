from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('processFile', '0005_uploadjob'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS product_import_staging (
                id BIGSERIAL PRIMARY KEY,
                job_id UUID NOT NULL,
                sku TEXT,
                name TEXT,
                description TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
            );
            CREATE INDEX IF NOT EXISTS idx_staging_job ON product_import_staging(job_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS idx_staging_job;
            DROP TABLE IF EXISTS product_import_staging;
            """
        )
    ]
