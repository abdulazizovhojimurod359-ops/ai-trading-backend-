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
    return {"status": "Server ishlamoqda!"}

@app.post("/analyze")
async def analyze_chart(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_image}"

        prompt = """
        Siz professional treydersiz. Grafikni tahlil qiling va faqat quyidagi JSON formatida javob bering:
        {
            "direction": "BUY yoki SELL",
            "reason": "Qisqa tahlil sababi",
            "pair": "Valyuta juftligi (masalan: EUR/USD)",
            "risk_reward": "1:3",
            "entry": "Kirish narxi",
            "stop_loss": "SL narxi",
            "take_profit": "TP narxi"
        }
        Faqat to'g'ri JSON berilsin, boshqa matn yozilmasin.
        """

        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-instruct",
            messages=[
                {"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": data_url}}]}
            ]
        )
        
        raw_json = json.loads(response.choices[0].message.content)
        return raw_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
