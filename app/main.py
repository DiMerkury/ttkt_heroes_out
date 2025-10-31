from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_game import router as game_router
from app.services.ws_manager import ws_manager

app = FastAPI(title="TTKT Heroes Out API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router, prefix="/game")

@app.on_event("startup")
async def on_startup():
    await ws_manager.startup()

@app.on_event("shutdown")
async def on_shutdown():
    await ws_manager.shutdown()

@app.get("/")
async def root():
    return {"status": "ok", "project": "TTKT Heroes Out"}
