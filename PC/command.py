import serial
import time
import json
import requests
import random
import re
import pyttsx3
import speech_recognition as sr

# Инициализация TTS
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if 'russian' in voice.name.lower() or 'irina' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break
engine.setProperty('rate', 190)

# Инициализация распознавания речи
recognizer = sr.Recognizer()

# Подключение к Serial
ser = serial.Serial('COM5', 115200, timeout=1)  # Укажи свой порт
time.sleep(2)

OLLAMA_API_URL = "http://localhost:11434/api/generate"

EMOTIONS = [
    "neutral", "angry_talking", "smile", "smile_love",
    "embarrassed", "scary", "happy", "sad",
    "surprise", "happy_circle", "talking"
]

TALKING_EMOTIONS = ["talking"]
FINAL_EMOTIONS = ["neutral"]

def detect_emotion_simple(text):
    text_lower = text.lower()
    if any(word in text_lower for word in ["ха", "ахах", "лол", "смешно"]):
        return "smile"
    if any(word in text_lower for word in ["люблю", "обожаю", "милая"]):
        return "smile_love"
    if any(word in text_lower for word in ["боюсь", "страшно", "ужас"]):
        return "scary"
    if any(word in text_lower for word in ["грустно", "печально", "жаль"]):
        return "sad"
    if any(word in text_lower for word in ["удивительно", "ого", "вау"]):
        return "surprise"
    if any(word in text_lower for word in ["стыдно", "смущаюсь", "неловко"]):
        return "embarrassed"
    if "?" in text:
        return "talking"
    if text.strip():
        return "talking"
    return "neutral"

def get_emotion_from_context(text):
    emotion = detect_emotion_simple(text)

    prompt = f"""
    Ты — дружелюбный виртуальный собеседник. Пользователь говорит с эмоцией: {emotion}.
    Ответь коротко и естественно на русском в этом настроении.
    Фраза пользователя: "{text}"

    Ответ строго в формате JSON:
    {{
        "emotion": "{emotion}",
        "text": "<естественный ответ>"
    }}
    """

    payload = {"model": "llama3.1:8b", "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        match = re.search(r'\{.*?\}', result, re.DOTALL)
        if match:
            emotion_data = json.loads(match.group())
            if "text" in emotion_data:
                return {"emotion": emotion, "text": emotion_data["text"]}
    except Exception as e:
        print(f"🔴 Ошибка при запросе к Ollama: {e}")

    return {"emotion": emotion, "text": "Что-то пошло не так, попробуй повторить!"}

def speak(text, ser, emotion):
    speech_duration = len(text) / 10.0 + 0.1
    command = {
        "emotion": emotion if emotion in TALKING_EMOTIONS else "talking",
        "duration": speech_duration,
        "intensity": 1.0,
        "volume": 1.25,
        "text": text,
        "anim_duration": 5,
        "mouth_speed": max(0.1, min(0.5, 0.1 + (len(text) / 50)))
    }
    command_json = json.dumps(command) + "\r\n"
    ser.write(command_json.encode('utf-8'))
    time.sleep(0.1)

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"🔴 Ошибка при синтезе речи: {e}")

def recognize_speech():
    try:
        with sr.Microphone() as source:
            print("🎙️ Говори в микрофон...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language='ru-RU')
            print(f"🟢 Распознано: {text}")
            return text
    except Exception as e:
        print(f"🔴 Ошибка при распознавании: {e}")
        return ""

# Инициализация общения
initial = ser.readline().decode('utf-8').strip()
print(f"Initial: {initial}")
ser.write((json.dumps({"emotion": "neutral", "duration": 2.0, "intensity": 1.0, "volume": 0.3}) + "\r\n").encode('utf-8'))

input_choice = input("🎙️ Использовать микрофон? (да/нет): ").lower()
use_mic = input_choice == "да"

while True:
    if use_mic:
        user_input = recognize_speech()
    else:
        user_input = input("> ")

    if user_input.lower() == "q":
        break
    if not user_input:
        continue

    emotion_data = get_emotion_from_context(user_input)
    emotion = emotion_data["emotion"]
    llama_response = emotion_data["text"]

    print(f"\n🟢 Эмоция: {emotion}")
    print(f"🟢 Ответ: {llama_response}")

    if llama_response:
        speak(llama_response, ser, emotion)
        final_emotion = random.choice(FINAL_EMOTIONS)
        ser.write((json.dumps({"emotion": final_emotion, "duration": 2.0, "intensity": 1.0, "volume": 0.2}) + "\r\n").encode('utf-8'))
    else:
        ser.write((json.dumps({"emotion": emotion, "duration": 2.0, "intensity": 1.0, "volume": 1.22}) + "\r\n").encode('utf-8'))

    response = ser.readline().decode('utf-8').strip()
    print(f"Response: {response}")

ser.close()
print("Программа завершена.")
