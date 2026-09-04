import base64
import os
import json

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


@app.get("/")
async def root():
    return {"status": "ok", "service": "AI Trading Master", "analyze_endpoint": "/analyze"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode("utf-8")

    prompt = (
        "Analiz qil: Ushbu grafik rasmiga qarab trading signal ber. "
        "Javobni faqat va faqat quyidagi JSON formatida qaytar: "
        '{"signal": "BUY/SELL", "percentage": 85, "entry": "1.2345", "sl": "1.2300", "tp": "1.2400"}'
    )

    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        temperature=0.2,
    )

    raw_result = completion.choices[0].message.content or "{}"
    try:
        result = json.loads(raw_result.strip().replace("```json", "").replace("```", ""))
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=502,
            content={"detail": "AI javobi JSON formatida emas", "raw_result": raw_result},
        )

    # Frontend kutayotgan nomlarga moslashtiramiz.
    return {
        "signal": result.get("signal", "BUY"),
        "trend": result.get("trend", ""),
        "win_rate_probability": f"{result.get('percentage', 0)}%",
        "buy_percentage": result.get("buy_percentage", result.get("percentage", 0)),
        "sell_percentage": result.get("sell_percentage", 100 - result.get("percentage", 0)),
        "pattern": result.get("pattern", "Noma'lum"),
        "entry_price": result.get("entry", "0.00"),
        "stop_loss": result.get("sl", "0.00"),
        "take_profit_1": result.get("tp1", result.get("tp", "0.00")),
        "take_profit_2": result.get("tp2", "0.00"),
    }
