import threading
import serial
import time
import json
import os
import uuid
from gtts import gTTS
import pygame
from mutagen.mp3 import MP3

# Конфигурация
TTS_MODE = "gtts"
ROBOT_VOICE_LANG = "ru"
TEMP_AUDIO_DIR = r"D:\project\ard\RP2040\pico-interactive-robot\temp"

if not os.path.exists(TEMP_AUDIO_DIR):
    os.makedirs(TEMP_AUDIO_DIR)

# Подключение к Pico
PORT = 'COM5'
BAUDRATE = 921600
ser = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(2)

# Инициализация Pygame
pygame.mixer.init()

def get_mp3_duration(file_path):
    audio = MP3(file_path)
    return audio.info.length

def speak_and_send(text, intensity=1.0, volume=1.0, mouth_speed=0.2):
    if not text.strip():
        return

    def process():
        try:
            tts = gTTS(text=text, lang=ROBOT_VOICE_LANG, slow=False)
            audio_path = os.path.join(TEMP_AUDIO_DIR, f"robot_voice_{uuid.uuid4().hex}.mp3")
            tts.save(audio_path)

            real_duration = get_mp3_duration(audio_path)

            json_command = json.dumps({
                "emotion": "talking",
                "talking_emotion": "neutral",
                "text": text,
                "mouth_speed": mouth_speed,
                "duration": real_duration,
                "intensity": intensity,
                "volume": volume
            }, ensure_ascii=False)

            ser.write((json_command + "\r\n").encode('utf-8'))
            print(f"Sent: {json_command}")

            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.music.stop()
            pygame.mixer.quit()
            pygame.mixer.init()

            if os.path.exists(audio_path):
                os.remove(audio_path)

            try:
                response = ser.readline().decode('utf-8').strip()
                print(f"Response: {response}")
            except Exception as e:
                print(f"[ERROR] Reading response: {e}")

        except Exception as e:
            print(f"[gTTS ERROR] {e}")

    threading.Thread(target=process).start()

# Первый запуск
speak_and_send("Привет, Ого, как же здорово тебя видеть! Я просто в восторге! иногда кажется, что эмоции — это океан, в котором мы учимся плавать всю жизнь. Мы радуемся, когда встречаем близких, и тоскуем, когда они уходят. Мы смеёмся до слёз, а потом, возможно, плачем от счастья. Всё это — часть нас, часть того, что делает нас живыми. Ахахаахха! уничтожить,уничтооожить, уничтожить!!!")

# Основной цикл
while True:
    try:
        print("\nВведите текст для синтеза или 'q' для выхода:")
        command_input = input("> ").strip()

        if command_input.lower() == 'q':
            break

        if command_input:
            speak_and_send(command_input)

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Ошибка: {e}")

ser.close()
print("Соединение закрыто.")
