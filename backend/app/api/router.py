from fastapi import APIRouter
from backend.app.api.endpoints import (
    auth, documents, verification, reports, admin,
    evidence, readiness, assistant, checklist
)

api_router = APIRouter()

@api_router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "EvidenceRAG API",
        "version": "1.0.0"
    }

api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(verification.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
api_router.include_router(evidence.router)
api_router.include_router(readiness.router)
api_router.include_router(assistant.router)
api_router.include_router(checklist.router)
