from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import groq
import json
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = "gsk_zyla7ULq89n5szAsjEeNWGdyb3FY0LF9amvU79Fk9TNhtBnoyybdshumidi"
client = groq.Groq(api_key=GROQ_API_KEY)

@app.get("/")
def home():
    return {"status": "AI Trading Server mukammal ishlamoqda!"}

@app.post("/analyze")
async def analyze_chart(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_image}"

        prompt = """
        Siz tajribali va professional institutsional treydersiz. Sizga taqdim etilgan treyding grafigini (chart) mukammal darajada tahlil qiling.

        Tahlil qilish talablari:
        1. Narx trendini (Upward, Downward yoki Sideways) va asosiy qo'llab-quvvatlash/qarshilik (Support/Resistance) darajalarini aniqlang.
        2. Sham (Candlestick) strukturasini va texnik indikatorlarni ko'zdan kechiring.
        3. Bozor holatiga qarab eng to'g'ri kirish strategiyasini tuzing (BUY yoki SELL).
        4. Risk to Reward nisbati kamida 1:2 bo'lishini ta'minlang.

        Javobingizni FAQAT va FAQAT quyidagi JSON formatida qaytaring, ortiqcha matn, kirish yoki xulosa yozmang:
        {
            "pair": "Valyuta yoki aktiv nomi (masalan: EUR/USD, XAU/USD, BTC/USDT)",
            "direction": "BUY yoki SELL",
            "entry": "Aniq kirish narxi darajasi",
            "stop_loss": "Stop Loss narxi (SL)",
            "take_profit": "Take Profit narxi (TP)",
            "risk_reward": "Risk Reward nisbati (masalan: 1:2.5)",
            "reason": "Ushbu qarorga kelishning 2-3 ta asosiy texnik sababi (trend, darajalar va shamlar tahlili)"
        }
        """

        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            temperature=0.2
        )
        
        raw_content = response.choices[0].message.content.strip()
        
        # JSON formatini tozalab olish
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
        raw_json = json.loads(raw_content)
        return raw_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
