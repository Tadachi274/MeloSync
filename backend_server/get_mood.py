from fastapi import FastAPI
from pydantic import BaseModel
import openai
from datetime import datetime
import os
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()

class HeartRate(BaseModel):
    heartrate: int  # 只接心跳速率

class EmotionInput(BaseModel):
    mood: str  # 例如 "HAPPY", "SAD", "NEUTRAL"

last_heart_rate = None
previous_heart_rate = None
heart_rate = []

client = openai.OpenAI()  # <<== 這裡定義一次

@app.get("/")
async def root():
    return {"message": "FastAPI server is running"}

def analyze_emotion_via_openai(heart_rate, positive):
    # prompt = f"""
    # 現在、ユーザの心拍は {current_bpm} bpmで、この前の心拍は {delta_bpm} bpmでした。
    # ユーザが選んだ気持ちは{positive}でした。
    # 以上の状態により、ユーザは今、「Happy/Excited」「Angry/Frustrated」「Tired/Sad」「Relax/Chill」、四つの感情の中で、どの感情ですか？
    # """

    prompt = f"""
    現在、ユーザの心拍の時系列は {heart_rate} でした。
    ユーザが選んだ気分は{positive}でした。
    心拍の時系列と気分により、ユーザは今、Happy/Excited (positive, 心拍数が高い), Angry/Frustrated (negative, 心拍数が高い), Tired/Sad (negative, 心拍数が低い), Relax/Chill (positive, 心拍数が低い)、四つの感情の中で、どの感情ですか？
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは感情推定の専門家です。ユーザの心拍データと気分により、Happy/Excited (=1), Angry/Frustrated (=2), Tired/Sad (=3), Relax/Chill (=4)から一つの感情を返信してください。フォーマット：1, 2, 3, 4"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


@app.post("/heartrate")
async def receive_heartrate(data: HeartRate):
    #global last_heart_rate, previous_heart_rate
    global heart_rate

    current_timestamp = datetime.utcnow().isoformat()

    # 更新前一筆心跳為舊的 last_heart_rate
    # if last_heart_rate is not None:
    #     previous_heart_rate = last_heart_rate

    # 存新資料
    # last_heart_rate = {
    #     "heartrate": data.heartrate,
    #     "timestamp": current_timestamp
    # }
    heart_rate.append({
        "heartrate": data.heartrate,
        "timestamp": current_timestamp
    })

    print(f"[POST /heartrate] Received bpm: {data.heartrate} at {current_timestamp}")

    return {
        "status": "received",
        "heartrate": data.heartrate,
        "timestamp": current_timestamp
    }

@app.post("/analyze_emotion")
async def analyze_emotion(data: EmotionInput):
    # if last_heart_rate is None:
    #     return {"error": "尚未收到任何心跳資料"}

    if heart_rate is []:
         return {"error": "尚未收到任何心跳資料"}
    
    if data.mood == "SAD":
        user_mood = "NEGATIVE"
    elif data.mood == "HAPPY":
        user_mood = "POSITIVE"
    else:
        user_mood = data.mood
    #current_bpm = last_heart_rate['heartrate']

    # if previous_heart_rate is None:
    #     delta_bpm = 0
    # else:
    #     delta_bpm = current_bpm - previous_heart_rate['heartrate']
    

    emotion = analyze_emotion_via_openai(heart_rate, positive=user_mood)

    print(f"[POST /analyze_emotion] Received mood: {data.mood} and the result is {emotion}.")
    return {"emotion": emotion}

# 用 uvicorn 執行：uvicorn fastAPI.main:app --reload --host 0.0.0.0 --port 5000
# curl -X POST "http://127.0.0.1:5000/heartrate" -H "Content-Type: application/json" -d "{\"heartrate\": 70}"
# curl -X POST "http://127.0.0.1:5000/analyze_emotion" -H "Content-Type: application/json" -d "{\"mood\":\"negative\"}"