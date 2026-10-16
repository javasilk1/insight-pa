from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import pratiche

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Benvenuto nel backend FastAPI per InsightPA!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(pratiche.router)
