# command_ai.py
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

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"  

MODEL_NAME = "nousresearch/deephermes-3-mistral-24b-preview:free"

EMOTIONS = [
    "neutral", "angry_talking", "smile", "smile_love",
    "embarrassed", "scary", "happy", "sad",
    "surprise", "happy_circle", "talking"
]

TALKING_EMOTIONS = ["talking"]
FINAL_EMOTIONS = ["neutral"]

def detect_emotion_simple(text):
    if not text:
        return "neutral"
        
    text_lower = text.lower()
    
    # Словарь эмоций и их триггеров
    emotion_triggers = {
        "smile": ["ха", "ахах", "лол", "смешно", "весело", "забавно", "хехе"],
        "smile_love": ["люблю", "обожаю", "милая", "❤️", "♥️", "милый", "прелесть", "красота"],
        "scary": ["боюсь", "страшно", "ужас", "жутко", "кошмар", "паника"],
        "sad": ["грустно", "печально", "жаль", "тоска", "грусть", "печаль", "плохо"],
        "surprise": ["удивительно", "ого", "вау", "неожиданно", "поразительно", "невероятно", "!"],
        "embarrassed": ["стыдно", "смущаюсь", "неловко", "извини", "прости", "стесняюсь"],
        "angry_talking": ["злой", "злость", "раздражает", "бесит", "ненавижу", "гнев"],
        "happy": ["радость", "счастье", "прекрасно", "супер", "отлично", "класс", "круто"]
    }
    
    # Проверка на вопросительные предложения
    if "?" in text:
        # Если в вопросе есть эмоциональные триггеры, используем соответствующую эмоцию
        for emotion, triggers in emotion_triggers.items():
            if any(trigger in text_lower for trigger in triggers):
                return emotion
        return "talking"  # Если нет эмоциональных триггеров, используем обычный talking

    # Проверка на восклицательные предложения
    if "!" in text:
        # Проверяем наличие эмоциональных триггеров
        for emotion, triggers in emotion_triggers.items():
            if any(trigger in text_lower for trigger in triggers):
                return emotion
        return "happy"  # По умолчанию для восклицательных предложений

    # Проверка на эмоциональные триггеры
    max_triggers = 0
    detected_emotion = "neutral"
    
    for emotion, triggers in emotion_triggers.items():
        trigger_count = sum(1 for trigger in triggers if trigger in text_lower)
        if trigger_count > max_triggers:
            max_triggers = trigger_count
            detected_emotion = emotion
    
    # Если найдены триггеры, возвращаем соответствующую эмоцию
    if max_triggers > 0:
        return detected_emotion
        
    # Если есть текст, но нет явных эмоциональных маркеров
    if text.strip():
        return "talking"
        
    return "neutral"

def get_emotion_from_context(text):
    emotion = detect_emotion_simple(text)

    prompt = f"""
Ты — дружелюбный виртуальный собеседник. Пользователь говорит с эмоцией: {emotion}.
Ответь коротко и естественно на русском в этом настроении.
Фраза пользователя: "{text}"

Ответь ТОЛЬКО в формате JSON без лишнего текста:
{{
    "emotion": "{emotion}",
    "text": "твой ответ здесь"
}}

Важно: Не добавляй никакого текста до или после JSON.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]["content"]
        print(f"🤖 AI response: {message}")
        match = re.search(r'\{.*?\}', message, re.DOTALL)
        if match:
            emotion_data = json.loads(match.group())
            if "text" in emotion_data:
                result = {"emotion": emotion, "text": emotion_data["text"]}
                print(f"✨ Final response: {result}")
                return result
    except Exception as e:
        print(f"🔴 Ошибка при запросе к OpenRouter: {e}")

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
