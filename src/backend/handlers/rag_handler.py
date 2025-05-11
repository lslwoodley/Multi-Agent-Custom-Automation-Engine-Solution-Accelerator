from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from core.security import get_current_user_claims, get_current_user_groups
from app_config import config

router = APIRouter(
    prefix="/api/rag",
    tags=["rag"],
)

@router.get("/{domain}/query")
async def query_rag_domain(
    domain: str,
    q: str,
    user_groups: List[str] = Depends(get_current_user_groups),
    user_claims: Dict[str, Any] = Depends(get_current_user_claims)
):
    # 1. Get Cosmos DB container
    try:
        cosmos_db = config.get_cosmos_database_client()
        container = cosmos_db.get_container_client("DomainPermissions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cosmos DB connection error: {str(e)}")

    # 2. Fetch Domain Permission Document
    try:
        domain_permission = container.read_item(item=domain, partition_key=domain)
        allowed_group_ids = domain_permission.get("allowedGroupIds", [])
    except Exception:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not configured for access.")

    # 3. Check RBAC - Ensure user is in at least one allowed group
    if not any(group in allowed_group_ids for group in user_groups):
        raise HTTPException(status_code=403, detail=f"Access denied for domain '{domain}'.")

    # 4. Continue with RAG logic (Placeholder Response)
    return {
        "message": f"Access granted to '{domain}' for query '{q}'. RAG results coming soon.",
        "user_groups": user_groups,
        "allowed_groups": allowed_group_ids
    }
