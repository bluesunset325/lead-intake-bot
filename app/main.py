import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

telegram_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    
    from app.bot import create_application
    telegram_app = create_application()
    
    await telegram_app.initialize()
    print("Бот инициализирован")
    
    yield
    
    await telegram_app.shutdown()
    print("Бот остановлен")


app = FastAPI(
    title="Lead Intake Bot",
    description="Telegram бот для приема заявок",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """для health check на Render"""
    return {"status": "ok", "service": "lead-intake-bot"}


@app.post("/webhook")
async def webhook_handler(
    request: Request,
    x_webhook_secret: str = Header(None)
):
    expected_secret = os.getenv("WEBHOOK_SECRET")
    if expected_secret and x_webhook_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    data = await request.json()
    
    if telegram_app:
        await telegram_app.process_update(data)
    
    # Telegram ждёт 200 в любом случае
    return Response(status_code=200)


@app.get("/")
async def root():
    return {
        "service": "Lead Intake Bot",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook"
        }
    }
