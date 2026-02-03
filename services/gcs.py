from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account

import config

# Initialize client with service account credentials
_credentials = service_account.Credentials.from_service_account_file(
    config.GCS_CREDENTIALS_JSON
)
_client = storage.Client(credentials=_credentials, project=_credentials.project_id)
_bucket = _client.bucket(config.GCS_BUCKET_NAME)


def upload_pdf(doc_id: str, filename: str, content: bytes) -> str:
    """
    Upload a PDF to GCS.
    Returns the GCS URL.
    """
    blob_path = f"pdfs/{doc_id}/{filename}"
    blob = _bucket.blob(blob_path)
    blob.upload_from_string(content, content_type="application/pdf")
    return f"gs://{config.GCS_BUCKET_NAME}/{blob_path}"


def upload_image(doc_id: str, image_id: str, content: bytes) -> str:
    """
    Upload a cropped image to GCS.
    Returns a signed URL valid for 7 days.
    """
    from datetime import timedelta

    blob_path = f"images/{doc_id}/{image_id}.png"
    blob = _bucket.blob(blob_path)
    blob.upload_from_string(content, content_type="image/png")

    # Generate signed URL (valid for 7 days)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(days=7),
        method="GET",
    )
    return url


def download_pdf(doc_id: str, filename: str) -> bytes:
    """Download a PDF from GCS."""
    blob_path = f"pdfs/{doc_id}/{filename}"
    blob = _bucket.blob(blob_path)
    return blob.download_as_bytes()


def delete_document_files(doc_id: str) -> int:
    """
    Delete all files for a document (PDF and images).
    Returns count of deleted files.
    """
    count = 0

    # Delete PDFs
    for blob in _bucket.list_blobs(prefix=f"pdfs/{doc_id}/"):
        blob.delete()
        count += 1

    # Delete images
    for blob in _bucket.list_blobs(prefix=f"images/{doc_id}/"):
        blob.delete()
        count += 1

    return count


def list_images(doc_id: str) -> list[str]:
    """List all image URLs for a document."""
    urls = []
    for blob in _bucket.list_blobs(prefix=f"images/{doc_id}/"):
        urls.append(blob.public_url)
    return urls


def get_pdf_url(doc_id: str) -> str | None:
    """
    Get a signed URL for a document's PDF.

    Args:
        doc_id: Document record ID

    Returns:
        Signed URL valid for 1 hour, or None if not found
    """
    from datetime import timedelta

    # Find the PDF blob (there should be only one per doc)
    blobs = list(_bucket.list_blobs(prefix=f"pdfs/{doc_id}/"))
    if not blobs:
        return None

    blob = blobs[0]
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET",
    )


def get_page_image_url(doc_id: str, page_num: int) -> str | None:
    """
    Get a signed URL for a page image.

    Args:
        doc_id: Document record ID
        page_num: 1-indexed page number

    Returns:
        Signed URL valid for 1 hour, or None if not found
    """
    from datetime import timedelta

    blob_path = f"images/{doc_id}/page_{page_num}.png"
    blob = _bucket.blob(blob_path)

    if not blob.exists():
        return None

    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET",
    )
