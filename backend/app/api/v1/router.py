# pyrefly: ignore [missing-import]
from fastapi import APIRouter

api_v1_router = APIRouter()


@api_v1_router.get("/")
async def root():
    return {"message": "AI Knowledge Assistant API v1"}


from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router

api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents"])

# Routers will be included here as each phase is built:
# from app.api.v1.chat import router as chat_router
# from app.api.v1.admin import router as admin_router
# from app.api.v1.evaluation import router as evaluation_router
#
# api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
# api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
# api_v1_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
# api_v1_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
# api_v1_router.include_router(evaluation_router, prefix="/evaluation", tags=["Evaluation"])
