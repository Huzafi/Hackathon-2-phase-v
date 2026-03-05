"""FastAPI application entry point."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import time
import logging
import asyncio
from .core.database import create_db_and_tables
from .core.kafka import cleanup_kafka_clients
from .core.dapr import cleanup_dapr_client
from .services.event_consumer import get_event_consumer, cleanup_event_consumer
from .api import auth, todos, chat, conversations, tags, recurrence, reminders, search


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Background task for consuming events
event_consumer_task = None


async def consume_events_background():
    """Background task to consume events from Kafka."""
    consumer = get_event_consumer()
    await consumer.start_consuming()


async def retry_unprocessed_events_background():
    """Background task to retry unprocessed events periodically."""
    consumer = get_event_consumer()
    while True:
        try:
            await asyncio.sleep(60)  # Run every 60 seconds
            count = await consumer.retry_unprocessed_events()
            if count > 0:
                logger.info(f"Retried {count} unprocessed events")
        except Exception as e:
            logger.error(f"Error in retry background task: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Todo Backend API...")
    create_db_and_tables()
    logger.info("Database tables created successfully")
    
    # Start event consumer background task
    global event_consumer_task
    event_consumer_task = asyncio.create_task(consume_events_background())
    logger.info("Event consumer background task started")
    
    # Start retry background task
    retry_task = asyncio.create_task(retry_unprocessed_events_background())
    logger.info("Retry background task started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Todo Backend API...")
    
    # Stop event consumer
    if event_consumer_task:
        event_consumer_task.cancel()
        try:
            await event_consumer_task
        except asyncio.CancelledError:
            pass
    
    # Stop retry task
    retry_task.cancel()
    try:
        await retry_task
    except asyncio.CancelledError:
        pass
    
    # Cleanup Kafka clients
    await cleanup_kafka_clients()
    logger.info("Kafka clients disconnected")
    
    # Cleanup Dapr client
    cleanup_dapr_client()
    logger.info("Dapr client disconnected")
    
    # Cleanup event consumer
    await cleanup_event_consumer()
    logger.info("Event consumer cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="Todo Backend API",
    description="A multi-user todo application backend with JWT authentication",
    version="1.0.0",
    contact={
        "name": "Todo Backend Team",
        "url": "https://github.com/Huzafi/Hackathon-2-Phase-II",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(tags.router)
app.include_router(recurrence.router)
app.include_router(reminders.router)
app.include_router(search.router)
app.include_router(chat.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests with method, path, status code, and duration."""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return user-friendly error."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later."
        }
    )


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


# HTTP exception handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Todo Backend API",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    from .core.kafka import get_producer, get_consumer
    from .core.config import settings

    kafka_status = "connected" if get_producer().is_connected else "disconnected"
    consumer_status = "connected" if get_consumer().is_connected else "disconnected"
    dapr_status = "enabled" if settings.enable_dapr else "disabled"

    return {
        "status": "healthy",
        "services": {
            "kafka_producer": kafka_status,
            "kafka_consumer": consumer_status,
            "dapr": dapr_status,
            "event_sourcing": "enabled" if settings.enable_event_sourcing else "disabled",
        }
    }
