import threading
import serial
import time
import json
import os
import pygame

# Конфигурация
VOICE_DIR = r"D:\project\ard\RP2040\pico-interactive-robot\voice"
PORT = 'COM5'
BAUDRATE = 921600

if not os.path.exists(VOICE_DIR):
    raise FileNotFoundError(f"Папка {VOICE_DIR} не найдена")

ser = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(0.5)

pygame.mixer.init(frequency=22050, size=-16, channels=1)
#output_robot_1.wav
AUDIO_TEXT_MAP = [
    {
        "file": "output_robot_1.wav",
        "text": "Внима-а-ние, бойцы-ы ретро-о-геймеры-ы!",
        "emotion": "talking",
        "talking_emotion": "neutral",
        "mouth_speed": 1.0,
        "anim_duration": 1
    },



    # {"file": "1_robot.wav", "emotion": "talking", "talking_emotion": "smile", "text": "Под Лунным Деревом жила маленькая девочка по имени Лера.", "mouth_speed": 0.6,},
    # {"file": "1_robot.wav", "emotion": "talking", "talking_emotion": "angry", "text": "Под Лунным Деревом жила маленькая девочка по имени Лера.", "mouth_speed": 0.6,},
    # {"file": "1_robot.wav", "emotion": "talking", "talking_emotion": "smile_tricky", "text": "Под Лунным Деревом жила маленькая девочка по имени Лера.", "mouth_speed": 1.5,},
    # {"file": "1_robot.wav", "emotion": "talking", "talking_emotion": "tricky", "text": "Под Лунным Деревом жила маленькая девочка по имени Лера.", "mouth_speed": 1.5, "duration": 6.0,"anim_duration": 2},
    # {"file": "1_robot.wav", "emotion": "talking", "talking_emotion": "smile", "text": "Под Лунным Деревом жила маленькая девочка по имени Лера.", "mouth_speed": 1.5, "duration": 6.0, "anim_duration": 2},
    # {"file": "1_robot.wav", "emotion": "talking", "talking_emotion": "ha", "text": "Под Лунным Деревом жила маленькая девочка по имени Лера.", "mouth_speed": 1.5, "duration": 6.0, "anim_duration": 2},

    # {"file": "happy.wav", "emotion": "scary", "duration": 6.0, "anim_duration": 8, "speed": 0.9},
    # {"emotion": "neutral", "duration": 6.0, "anim_duration": 3},
    # {"emotion": "smile", "duration": 6.0, "anim_duration": 8},
    # {"emotion": "smile_love", "duration": 6.0, "anim_duration": 8},
    # {"emotion": "scary", "duration": 6.0, "anim_duration": 8},
    # {"emotion": "happy", "duration": 6.0, "anim_duration": 8},
    # {"emotion": "sad", "duration": 6.0, "anim_duration": 8},
    # {"emotion": "surprise", "duration": 6.0, "anim_duration": 8},
    # {
    #     "file": "happy.wav",
    #     "text": "Привет, ого, как же здорово тебя видеть! Я просто в восторге! иногда кажется, что эмоции",
    #     "emotion": "talking",
    #     "talking_emotion": "happy",
    #     "mouth_speed": 1.5,
    #     "anim_duration": 2
    # },
    # {
    #     "file": "output_robot.wav",
    #     "text": "Привет, ого, как же здорово тебя видеть! Я просто в восторге! иногда кажется, что эмоции — это океан, в котором мы учимся плавать всю жизнь. Мы радуемся, когда встречаем близких, и тоскуем, когда они уходят. Мы смеёмся до слёз, а потом, возможно, плачем от счастья. Всё это — часть нас, часть того, что делает нас живыми. Ахахаахха! уничтожить,уничтооожить, уничтожить!!!",
    #     "emotion": "talking",
    #     "talking_emotion": "neutral",
    #     "mouth_speed": 1.5,
    #     "anim_duration": 1
    # },
]

def get_wav_duration(file_path):
    try:
        audio = pygame.mixer.Sound(file_path)
        return audio.get_length()
    except Exception as e:
        print(f"[ERROR] Failed to get duration of {file_path}: {e}")
        return 1.0

def play_audio_and_send(text, audio_file, emotion, talking_emotion, mouth_speed=1.5, anim_duration=0.5, intensity=1.0, volume=1.0):
    if not text.strip():
        print(f"Ошибка: текст пустой.")
        return

    def process():
        try:
            real_duration = get_wav_duration(audio_file) if audio_file and os.path.exists(audio_file) else anim_duration

            json_command = json.dumps({
                "emotion": emotion,
                "talking_emotion": talking_emotion,
                "text": text,
                "mouth_speed": mouth_speed,
                "duration": real_duration,
                "anim_duration": anim_duration,
                "intensity": intensity,
                "volume": volume
            }, ensure_ascii=False)

            ser.write((json_command + "\r\n").encode('utf-8'))
            print(f"Sent: {json_command}")

            time.sleep(1)  # Пауза для Pico перед началом воспроизведения

            if audio_file and os.path.exists(audio_file):
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.01)
                pygame.mixer.music.stop()

            try:
                response = ser.readline().decode('utf-8').strip()
                print(f"Response: {response}")
            except Exception as e:
                print(f"[ERROR] Reading response: {e}")

        except Exception as e:
            print(f"[Audio Playback ERROR] {e}")

    threading.Thread(target=process).start()

# Основной цикл
for audio_entry in AUDIO_TEXT_MAP:
    # Проверяем наличие ключа "text"
    text = audio_entry.get("text", "Текст не задан")

    audio_file = os.path.join(VOICE_DIR, audio_entry["file"]) if "file" in audio_entry else None
    emotion = audio_entry["emotion"]
    talking_emotion = audio_entry.get("talking_emotion", "neutral")
    mouth_speed = audio_entry.get("mouth_speed", 1.5)
    anim_duration = audio_entry.get("anim_duration", 0.5)

    play_audio_and_send(text, audio_file, emotion, talking_emotion, mouth_speed, anim_duration)

    pause = get_wav_duration(audio_file) if audio_file and os.path.exists(audio_file) else anim_duration
    time.sleep(pause + 0.5)

pygame.mixer.quit()
ser.close()
print("Соединение закрыто.")