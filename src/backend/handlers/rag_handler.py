from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/api/rag",
    tags=["rag"],
)

@router.get("/{domain}/query")
async def query_rag_domain(domain: str, q: str):
    """
    Minimal RAG query handler.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    
    # Placeholder response
    return {
        "message": f"Received query '{q}' for domain '{domain}'. RAG response coming soon."
    }
