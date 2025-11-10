from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.api.v1 import api_router
import traceback

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware - ДОЛЖЕН быть ПЕРВЫМ
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Обработчик исключений для правильной отправки CORS заголовков
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={"Access-Control-Allow-Origin": "*"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        error_detail = {
            "detail": str(exc),
            "traceback": traceback.format_exc()
        }
    else:
        error_detail = {"detail": "Внутренняя ошибка сервера"}
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_detail,
        headers={"Access-Control-Allow-Origin": "*"}
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Wholesale Aggregator API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

