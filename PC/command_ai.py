# AI интерактивный робот управляет через порт COM5 RP2040 Raspberry Pi Pico Bootloader v3.0 v1.0
# Для работы с голосом используется библиотека gtts
# Для работы с аудио используется библиотека pydub
# Для работы с сетью используется библиотека requests
# Для работы с потоками используется библиотека threading
# Для работы с UUID используется библиотека uuid
# Для работы с временными файлами используется библиотека os
# Для работы с JSON используется библиотека json
# Для работы с распознаванием речи используется библиотека speech_recognition
# GIThab: https://github.com/stroggfaer/pico-interactive-robot/tree/main
# Автор: Rendzhi
# command_ai.py
import serial
import time
import json
import requests
import random
import re
import speech_recognition as sr
import threading
import os
import uuid
from gtts import gTTS
import pygame
import wave
import contextlib
from pydub import AudioSegment
import scipy.io.wavfile as wavfile
import numpy as np
from requests.exceptions import HTTPError

HAS_MODE_AI = False  # True — AI/микрофон, False — только AUDIO_TEXT_MAP
#Test Эмоция;
AUDIO_TEXT_MAP = [
    {
        "text": "Привет! Я интерактивный демонстрационный робот. Я умею говорить и показывать эмоции.",
        "emotion": "talking",
        "talking_emotion": "neutral",
        "mouth_speed": 0.3,
        "duration": 6.0,
        "anim_duration": 1
    },
    # Характер эмоций для AUDIO_TEXT_MAP (только название характера)
    { "text": "Грустный", "emotion": "sad", "duration": 5.0, "anim_duration": 5},
    { "text": "Веселый", "emotion": "happy", "duration": 5.0, "anim_duration": 5},
    { "text": "Страшный", "emotion": "scary", "duration": 5.0, "anim_duration": 5},
    { "text": "Удивленный", "emotion": "surprise", "duration": 5.0, "anim_duration": 5},
    { "text": "Смущенный", "emotion": "embarrassed", "duration": 5.0, "anim_duration": 5},
    { "text": "Влюбленный", "emotion": "smile_love", "duration": 5.0, "anim_duration": 5},
    # Примеры talking_emotion с разными вариантами
    {
        "text": "Я могу говорить с разными эмоциями. Сейчас я говорю сердито!",
        "emotion": "talking",
        "talking_emotion": "angry",
        "mouth_speed": 0.7,
        "duration": 4.0,
        "anim_duration": 1
    },
    {
        "text": "Посмотри, как я хитро улыбаюсь, когда говорю!",
        "emotion": "talking",
        "talking_emotion": "smile_tricky",
        "mouth_speed": 0.5,
        "duration": 4.0,
        "anim_duration": 1
    },
    {
        "text": "Я могу быть очень озорным, когда разговариваю!",
        "emotion": "talking",
        "talking_emotion": "tricky",
        "mouth_speed": 0.6,
        "duration": 4.0,
        "anim_duration": 1
    },
    {
        "text": "Я могу говорить с широкой улыбкой!",
        "emotion": "talking",
        "talking_emotion": "smile",
        "mouth_speed": 0.8,
        "duration": 4.0,
        "anim_duration": 1
    },
    {
        "text": "Ха-ха-ха! Я смеюсь и говорю одновременно!",
        "emotion": "talking",
        "talking_emotion": "ha",
        "mouth_speed": 1.0,
        "duration": 3.0,
        "anim_duration": 1
    },
    {
        "text": "Теперь ты можешь говорить со мной через микрофон! Просто скажи что-нибудь, и я отвечу тебе голосом и эмоциями. Удачи)",
        "emotion": "talking",
        "talking_emotion": "neutral",
        "mouth_speed": 0.7,
        "duration": 5.0,
        "anim_duration": 1
    },
]

# Конфигурация
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = ""
MODEL_NAME = "deepseek/deepseek-chat" #"nousresearch/deephermes-3-mistral-24b-preview:free"
ROBOT_VOICE_EFFECT = 70 # Чем выше значение, тем "тоньше" и более синтетический голос

TTS_MODE = "gtts"
ROBOT_VOICE_LANG = "ru"
TEMP_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "temp") # Путь к папке для временных файлов


if not os.path.exists(TEMP_AUDIO_DIR):
    os.makedirs(TEMP_AUDIO_DIR)

pygame.mixer.init()

ser = serial.Serial('COM5', 115200, timeout=1)
time.sleep(2)
if HAS_MODE_AI:
    recognizer = sr.Recognizer()

TALKING_EMOTIONS = ["talking"]
FINAL_EMOTIONS = ["neutral"]

def get_wav_duration(file_path):
    with contextlib.closing(wave.open(file_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        return duration

def apply_robot_effect(wav_path):
    sample_rate, data = wavfile.read(wav_path)
    t = np.linspace(0, len(data) / sample_rate, num=len(data))
    modulator = np.sin(2 * np.pi * ROBOT_VOICE_EFFECT * t)
    robotized = (data * modulator).astype(data.dtype)
    robot_wav_path = wav_path.replace('.wav', '_robot.wav')
    wavfile.write(robot_wav_path, sample_rate, robotized)
    return robot_wav_path

def speak_and_send(text, ser, emotion, talking_emotion="neutral", intensity=1.0, volume=1.0, mouth_speed=0.2, sync=False, send_serial=True):
    if not text.strip():
        return

    def process():
        try:
            tts = gTTS(text=text, lang=ROBOT_VOICE_LANG, slow=False)
            unique_id = uuid.uuid4().hex
            mp3_path = os.path.join(TEMP_AUDIO_DIR, f"robot_voice_{unique_id}.mp3")
            wav_path = os.path.join(TEMP_AUDIO_DIR, f"robot_voice_{unique_id}.wav")
            tts.save(mp3_path)

            # Конвертируем MP3 в WAV
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(wav_path, format="wav")

            wav_path = apply_robot_effect(wav_path)

            real_duration = get_wav_duration(wav_path)

            if send_serial:
                json_command = json.dumps({
                    "emotion": emotion if emotion in TALKING_EMOTIONS else "talking",
                    "talking_emotion": talking_emotion,
                    "text": text,
                    "mouth_speed": mouth_speed,
                    "duration": real_duration,
                    "intensity": intensity,
                    "volume": volume
                })
                ser.write((json_command + "\r\n").encode('utf-8'))
                print(f"Sent: {json_command}")

            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.music.stop()
            pygame.mixer.quit()
            pygame.mixer.init()

            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)

            if send_serial:
                try:
                    response = ser.readline().decode('utf-8').strip()
                    print(f"Response: {response}")
                except Exception as e:
                    print(f"[ERROR] Reading response: {e}")

        except Exception as e:
            print(f"[gTTS ERROR] {e}")

    if sync:
        process()
    else:
        threading.Thread(target=process).start()

def detect_emotion_simple(text):
    if not text:
        return "neutral"
        
    text_lower = text.lower()
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

    if "?" in text:
        for emotion, triggers in emotion_triggers.items():
            if any(trigger in text_lower for trigger in triggers):
                return emotion
        return "talking"

    if "!" in text:
        for emotion, triggers in emotion_triggers.items():
            if any(trigger in text_lower for trigger in triggers):
                return emotion
        return "happy"

    max_triggers = 0
    detected_emotion = "neutral"
    
    for emotion, triggers in emotion_triggers.items():
        trigger_count = sum(1 for trigger in triggers if trigger in text_lower)
        if trigger_count > max_triggers:
            max_triggers = trigger_count
            detected_emotion = emotion

    if max_triggers > 0:
        return detected_emotion

    if text.strip():
        return "talking"

    return "neutral"

def get_emotion_from_context(text):
    emotion = detect_emotion_simple(text)
    # Определяем talking_emotion на основе emotion (оставляем только допустимые значения)
    allowed_talking_emotions = ["neutral", "angry", "smile_tricky", "tricky", "smile", "ha"]
    talking_emotion = emotion if emotion in allowed_talking_emotions else "neutral"
    prompt = f"""
    Ты — злой виртуальный собеседник. Пользователь говорит с эмоцией: {emotion}.
    Ответь коротко и естественно на русском в этом настроении.
    Фраза пользователя: \"{text}\"

    Ответь ТОЛЬКО в формате JSON без лишнего текста:
    {{
        \"emotion\": \"{emotion}\",
        \"text\": \"твой ответ здесь\"
    }}
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
                result = {"emotion": emotion, "talking_emotion": talking_emotion, "text": emotion_data["text"]}
                print(f"✨ Final response: {result}")
                return result
    except HTTPError as e:
        if hasattr(response, 'status_code') and response.status_code == 429:
            print("Превышен лимит запросов к AI. Попробуйте позже.")
            return {"emotion": emotion, "talking_emotion": "angry", "text": "Лимит запросов к OpenRouter превышен. Попробуйте позже."}
        else:
            print(f"🔴 Ошибка при запросе к OpenRouter: {e}")

    return {"emotion": emotion, "talking_emotion": "tricky", "text": "Что-то пошло не так, попробуй повторить!"}

def recognize_speech():
    try:
        with sr.Microphone() as source:
            print("🎙️ Говори в микрофон...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)
            text = recognizer.recognize_google(audio, language='ru-RU')
            print(f"🟢 Распознано: {text}")
            return text
    except Exception as e:
        print(f"🔴 Ошибка при распознавании: {e}")
        return ""

def change_speed(wav_path, speed=1.2):
    sound = AudioSegment.from_wav(wav_path)
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
         "frame_rate": int(sound.frame_rate * speed)
      })
    sound_with_altered_frame_rate = sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)
    new_path = wav_path.replace('.wav', f'_speed{speed}.wav')
    sound_with_altered_frame_rate.export(new_path, format="wav")
    return new_path

initial = ser.readline().decode('utf-8').strip()
print(f"Initial: {initial}")
ser.write((json.dumps({"emotion": "neutral", "duration": 2.0, "intensity": 1.0, "volume": 0.3}) + "\r\n").encode('utf-8'))

if HAS_MODE_AI:
    input_choice = input("🎙️ Использовать микрофон? (да/нет): ").lower()
    use_mic = input_choice == "да"
else:
    use_mic = False

if not HAS_MODE_AI:
    for audio_entry in AUDIO_TEXT_MAP:
        text = audio_entry.get("text", "Текст не задан")
        emotion = audio_entry["emotion"]
        talking_emotion = audio_entry.get("talking_emotion", "neutral")
        mouth_speed = audio_entry.get("mouth_speed", 1.5)
        anim_duration = audio_entry.get("anim_duration", 0.5)
        duration = audio_entry.get("duration", 1.0)

        try:
            # 1. Сгенерировать аудиофайл и узнать duration
            tts = gTTS(text=text, lang=ROBOT_VOICE_LANG, slow=False)
            unique_id = uuid.uuid4().hex
            mp3_path = os.path.join(TEMP_AUDIO_DIR, f"robot_voice_{unique_id}.mp3")
            wav_path = os.path.join(TEMP_AUDIO_DIR, f"robot_voice_{unique_id}.wav")
            tts.save(mp3_path)
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(wav_path, format="wav")
            wav_path = apply_robot_effect(wav_path)
            real_duration = get_wav_duration(wav_path)

            # 2. Отправить команду с duration
            if emotion == "talking":
                send_duration = real_duration
            else:
                send_duration = duration
            json_command = json.dumps({
                "emotion": emotion,
                "talking_emotion": talking_emotion,
                "text": text,
                "mouth_speed": mouth_speed,
                "duration": send_duration,
                "anim_duration": anim_duration,
                "intensity": 1.0,
                "volume": 1.0
            })
            ser.write((json_command + "\r\n").encode('utf-8'))
            print(f"Sent___: {json_command}")

            # 3. Сразу воспроизвести аудио (без sleep)
            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            pygame.mixer.init()

            # После воспроизведения аудио, удалить все файлы из TEMP_AUDIO_DIR
            try:
                for fname in os.listdir(TEMP_AUDIO_DIR):
                    fpath = os.path.join(TEMP_AUDIO_DIR, fname)
                    if os.path.isfile(fpath):
                        os.remove(fpath)
            except Exception as e:
                print(f"[ERROR] Cleaning temp dir: {e}")

            # 5. Дождаться ответа от RP2040 (если нужно)
            try:
                response = ser.readline().decode('utf-8').strip()
                print(f"Response: {response}")
            except Exception as e:
                print(f"[ERROR] Reading response: {e}")

            # 6. Пауза между эмоциями
            time.sleep(duration)
        except Exception as e:
            print(f"[ERROR] Audio/Emotion sync: {e}")

    ser.close()
    print("Программа завершена.")
    exit(0)

while True:
    if HAS_MODE_AI and use_mic:
        user_input = recognize_speech()
    else:
        user_input = input("> ")

    if user_input.lower() == "q":
        break
    if not user_input:
        continue

    emotion_data = get_emotion_from_context(user_input)
    emotion = emotion_data["emotion"]
    talking_emotion = emotion_data.get("talking_emotion", "neutral")
    llama_response = emotion_data["text"]

    print(f"\n🟢 Эмоция: {emotion}")
    print(f"🟢 Ответ: {llama_response}")
    mouth_speed = max(0.1, min(0.5, 0.1 + (len(llama_response) / 50)))
    if llama_response:
        speak_and_send(llama_response, ser, emotion, talking_emotion=talking_emotion, intensity=1.0, volume=1.0, mouth_speed=mouth_speed)
        final_emotion = random.choice(FINAL_EMOTIONS)
        ser.write((json.dumps({"emotion": final_emotion, "duration": 2.0, "intensity": 1.0, "volume": 0.2}) + "\r\n").encode('utf-8'))
    else:
        ser.write((json.dumps({"emotion": emotion, "duration": 2.0, "intensity": 1.0, "volume": 1.22}) + "\r\n").encode('utf-8'))

    response = ser.readline().decode('utf-8').strip()
    print(f"Response: {response}")
ser.close()
print("Программа завершена.")