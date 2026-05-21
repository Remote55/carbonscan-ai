"""File upload endpoints — stub for Phase 1.

TODO Phase 1:
- LAS/LAZ direct upload to Supabase Storage (chunked via tus protocol)
- Photogrammetry photo upload (multipart, 30-50 images)
- Validation (file size, extension, EXIF for photos)
- Create Job record + push to Queue
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/las", status_code=501)
async def upload_las() -> dict[str, str]:
    """Upload .las/.laz point cloud file. TODO: implement."""
    return {"message": "Not implemented — see TODO in upload.py"}


@router.post("/photos", status_code=501)
async def upload_photos() -> dict[str, str]:
    """Upload 30-50 photos for photogrammetry. TODO: implement."""
    return {"message": "Not implemented — see TODO in upload.py"}
