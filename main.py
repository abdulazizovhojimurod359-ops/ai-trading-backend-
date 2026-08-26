import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI(title="GetTrade Style AI Trading API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY topilmadi!")

genai.configure(api_key=GEMINI_API_KEY)

# GetTrade AI uslubidagi professional prompt (FAQAT BUY/SELL foizda, WAIT YO'Q)
PROMPT = """
You are a top-tier institutional crypto & forex trader with 15+ years of quantitative technical analysis experience. 
Analyze the uploaded chart screenshot like GetTrade AI.

CRITICAL INSTRUCTIONS:
1. DO NOT give "WAIT" or ambiguous signals. Choose either "BUY" (Bullish Trend) or "SELL" (Bearish Trend).
2. Assign exact signal strength percentages: buy_percentage + sell_percentage MUST equal 100%. (e.g., Buy: 82%, Sell: 18%).
3. Extract precise key levels from the chart: Entry Price, Stop Loss (SL), Take Profit 1 (TP1), Take Profit 2 (TP2).
4. Identify trend direction ("UPTREND" or "DOWNTREND") and chart pattern (e.g., Double Bottom, Bull Flag, Support Bounce).

Return ONLY raw JSON, no markdown around it (no ```json):
{
  "signal": "BUY",
  "buy_percentage": 82,
  "sell_percentage": 18,
  "trend": "UPTREND",
  "pattern": "Support Rejection & RSI Bullish Divergence",
  "entry_price": "1.0850",
  "stop_loss": "1.0810",
  "take_profit_1": "1.0910",
  "take_profit_2": "1.0980",
  "win_rate_probability": "84%"
}
"""

@app.get("/")
def home():
    return {"status": "ok", "message": "GetTrade AI Engine Active"}

@app.post("/analyze")
async def analyze_chart(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image_part = {
            "mime_type": file.content_type or "image/jpeg",
            "data": contents
        }
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([PROMPT, image_part])
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "").strip()

        data = json.loads(raw_text)
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Tahlil xatosi: {str(e)}")
