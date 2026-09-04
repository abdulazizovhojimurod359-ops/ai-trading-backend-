import base64
import json
import os
import re

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq

app = FastAPI(title="AI Trading Master API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")


@app.get("/")
async def root():
    return {"status": "ok", "service": "AI Trading Master", "analyze_endpoint": "/analyze"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Faqat JPG, PNG yoki WEBP rasm yuklang")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Rasm bo'sh")
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Rasm hajmi 10 MB dan kichik bo'lishi kerak")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY Render environment variables'da sozlanmagan")

    base64_image = base64.b64encode(contents).decode("utf-8")
    prompt = (
        "Ushbu trading grafikni tahlil qil. Faqat JSON qaytar, markdown ishlatma. "
        'Format: {"signal":"BUY yoki SELL","trend":"Bullish yoki Bearish",'
        '"percentage":85,"buy_percentage":70,"sell_percentage":30,'
        '"pattern":"...","entry":"...","sl":"...","tp1":"...","tp2":"..."}'
    )

    try:
        completion = Groq(api_key=api_key).chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{file.content_type};base64,{base64_image}"}},
                ]},
            ],
            temperature=0.2,
        )
    except Exception as error:
        return JSONResponse(status_code=502, content={"detail": f"AI xatosi: {str(error)}"})

    raw_result = completion.choices[0].message.content or "{}"
    cleaned = re.sub(r"```(?:json)?", "", raw_result).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    try:
        result = json.loads(match.group(0) if match else cleaned)
    except (json.JSONDecodeError, AttributeError):
        return JSONResponse(status_code=502, content={"detail": "AI javobi JSON formatida emas"})

    signal = str(result.get("signal", "BUY")).upper()
    percentage = max(0, min(100, int(float(result.get("percentage", 50)))))
    buy = max(0, min(100, int(float(result.get("buy_percentage", percentage if signal == "BUY" else 100 - percentage)))))
    return {
        "signal": signal if signal in {"BUY", "SELL"} else "BUY",
        "trend": result.get("trend", ""), "win_rate_probability": f"{percentage}%",
        "buy_percentage": buy, "sell_percentage": 100 - buy,
        "pattern": result.get("pattern", "Noma'lum"), "entry_price": result.get("entry", "0.00"),
        "stop_loss": result.get("sl", "0.00"), "take_profit_1": result.get("tp1", result.get("tp", "0.00")),
        "take_profit_2": result.get("tp2", "0.00"),
    }
