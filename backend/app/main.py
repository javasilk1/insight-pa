from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import buildings
from api import risk
from api import chat
from api import documents
from api import mock_generator
from api import risk_history
from core.config import settings
import asyncpg
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

@app.get("/")
async def root():
    return {"message": "Benvenuto nel backend FastAPI per InsightPA!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(buildings.router)
app.include_router(risk.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(mock_generator.router)
app.include_router(risk_history.router)
app.include_router(documents.router)
app.include_router(mock_generator.router)
