import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from backend.routers.auth import router as auth_router
from backend.routers.chat_history import router as chat_history_router
from backend.routers.document_processing import router as document_processing_router
from backend.routers.document_upload import router as document_upload_router
from backend.routers.question_answering import router as question_answering_router
from backend.routers.sessions import router as sessions_router
from backend.routers.streaming_responses import router as streaming_responses_router
from backend.routers.users import router as users_router
from backend.routers.vector_storage import router as vector_storage_router

from database.config import init_db

# Initialize FastAPI app
app = FastAPI(
    title="Aakaar Project",
    description="AI-powered web application backend",
    version="1.0.0",
)

# Initialize SlowAPI rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse({"detail": str(exc)}, status_code=429)

app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router, prefix='/api/auth', tags=['Auth'])
app.include_router(chat_history_router, prefix='/api/chat', tags=['Chat History'])
app.include_router(document_processing_router, prefix='/api', tags=['Document Processing'])
app.include_router(document_upload_router, prefix='/api/documents', tags=['Document Upload'])
app.include_router(question_answering_router, prefix='/api', tags=['Question Answering'])
app.include_router(sessions_router, prefix='/api/chat/sessions', tags=['Sessions'])
app.include_router(streaming_responses_router, prefix='/api', tags=['Streaming Responses'])
app.include_router(users_router, prefix='/api/auth/login', tags=['Users'])
app.include_router(vector_storage_router, prefix='/api/auth/login', tags=['Vector Storage'])

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse({"detail": exc.errors()}, status_code=422)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

# Health check endpoint
@app.get("/health")
async def health_check():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Lifespan context manager
@app.on_event("startup")
async def startup_event():
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    pass

# AI_ROUTER_INJECTION_POINT — do not remove this line
# AI layer — mounted by Agent 8B
from ai.routes import router as ai_router
app.include_router(ai_router, prefix='/api/ai', tags=['AI'])
