from pathlib import Path

from google.cloud import storage


def upload_to_gcs(bucket_name, source_file, destination_blob):
    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"Local file not found: {source_path}")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)

    blob.upload_from_filename(str(source_path))
    print(f"Uploaded {source_path} -> {destination_blob}")
