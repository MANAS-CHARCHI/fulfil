import csv, os, uuid
from django.conf import settings


def split_csv(path, chunk_size=50000):
    chunks = []
    upload_id = uuid.uuid4().hex

    # Absolute upload folder
    base_dir = os.path.join(settings.MEDIA_ROOT, "uploads", upload_id)
    os.makedirs(base_dir, exist_ok=True)

    # Correct, safe CSV reader
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)

        chunk_index = 1
        current_chunk = []

        for row in reader:
            current_chunk.append(row)

            if len(current_chunk) >= chunk_size:
                chunk_path = os.path.join(base_dir, f"chunk_{chunk_index}.csv")
                _write_chunk(chunk_path, header, current_chunk)
                chunks.append(chunk_path)
                current_chunk = []
                chunk_index += 1

        # Write last remainder chunk
        if current_chunk:
            chunk_path = os.path.join(base_dir, f"chunk_{chunk_index}.csv")
            _write_chunk(chunk_path, header, current_chunk)
            chunks.append(chunk_path)

    return chunks, base_dir



def _write_chunk(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
