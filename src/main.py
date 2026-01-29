import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.router import api
from src.exceptions import RecommendationException

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RecommendationException)
async def recommendation_exception_handler(
    request: Request, exc: RecommendationException
):
    """Global exception handler for all RecommendationException types."""
    logger.error("RecommendationException: %s", exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "type": exc.__class__.__name__,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions."""
    logger.exception("Unexpected error: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "type": "InternalServerError",
        },
    )


app.include_router(api.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
