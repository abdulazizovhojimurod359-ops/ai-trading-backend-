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
        Siz tajribali va professional treydersiz. Sizga taqdim etilgan treyding grafigini tahlil qiling.

        Tahlil talablari:
        1. Bozor ehtimolligini baholang: BUY ehtimolligi necha foiz (%) va SELL ehtimolligi necha foiz (%)? (Ikkalasining yig'indisi 100% bo'lsin).
        2. Qaysi foiz yuqori bo'lsa, o'sha yo'nalishni tanlang (BUY yoki SELL).
        3. Grafik kelajakda qanday harakat qilishi haqida qisqa va aniq BASHORAT (prognoz) bering.

        Javobni FAQAT va FAQAT ushbu JSON formatida qaytaring:
        {
            "pair": "Aktiv nomi (masalan: EUR/USD)",
            "buy_percentage": 75,
            "sell_percentage": 25,
            "direction": "BUY",
            "entry": "Kirish narxi",
            "stop_loss": "Stop Loss narxi",
            "take_profit": "Take Profit narxi",
            "prediction": "Grafik kelajakda qanday harakatlanishi haqida qisqa bashorat (masalan: Narx qarshilik darajasini yorib o'tib, yuqoriga qarab harakatni davom ettirishi kutilmoqda)"
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
        
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
        return json.loads(raw_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
