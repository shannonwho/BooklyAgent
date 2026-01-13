"""Bookly - Online Bookstore with AI Customer Support API."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data.database import init_db, AsyncSessionLocal, engine
from data.seed_books import seed_books
from data.seed_users import seed_users
from data.seed_orders import seed_orders, seed_policies

from api import auth, books, cart, orders, profile, websocket
from telemetry import init_telemetry
from telemetry.config import instrument_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Initialize telemetry
    environment = os.getenv("ENVIRONMENT", "development")
    init_telemetry(
        service_name="bookly-support-agent",
        service_version="1.0.0",
        environment=environment
    )

    # Instrument the FastAPI app with OpenTelemetry
    instrument_app(app, engine=engine.sync_engine if hasattr(engine, 'sync_engine') else None)

    # Startup: Initialize database and seed data
    print("Initializing database...")
    await init_db()

    # Seed data if database is empty
    async with AsyncSessionLocal() as session:
        await seed_books(session, count=500)
        await seed_users(session)
        await seed_orders(session)
        await seed_policies(session)

    print("Database initialized and seeded!")

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Bookly API",
    description="Online Bookstore with AI Customer Support",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(books.router, prefix="/api/books", tags=["Books"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Bookly API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
