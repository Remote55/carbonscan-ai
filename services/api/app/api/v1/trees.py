"""Tree CRUD + spatial query endpoints — stub for Phase 1.

TODO Phase 1:
- GET /trees — list with spatial filter (lat/lon/radius_km)
- GET /trees/{id} — detail
- POST /trees — create (called by ML worker)
- PATCH /trees/{id}/verify — auditor verification
- DELETE /trees/{id} — owner only
- GET /trees/{id}/point-cloud — pre-signed URL
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", status_code=501)
async def list_trees() -> dict[str, str]:
    """List trees with optional spatial filter. TODO: implement."""
    return {"message": "Not implemented — see TODO in trees.py"}


@router.get("/{tree_id}", status_code=501)
async def get_tree(tree_id: str) -> dict[str, str]:
    """Get tree by ID. TODO: implement."""
    return {"message": f"Not implemented — tree_id={tree_id}"}
