import base64
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


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

    return {"result": completion.choices[0].message.content}
