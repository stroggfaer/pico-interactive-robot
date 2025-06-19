import serial
import time
import json
import pyttsx3

# Функция подсчета слогов
VOWELS = "аеёиоуыэюяaeiouy"

def count_syllables(text):
    return sum(1 for char in text.lower() if char in VOWELS) or 1

def calculate_duration(text, rate=200):
    syllables = count_syllables(text)
    base_duration_ms = syllables * 180
    scale_factor = 200 / rate
    duration_ms = base_duration_ms * scale_factor
    return duration_ms / 1000

# Инициализация TTS движка
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if 'russian' in voice.name.lower() or 'irina' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break
engine.setProperty('rate', 200)

# Подключение к Pico
PORT = 'COM5'
BAUDRATE = 921600
ser = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(2)

# Читаем приветственное сообщение
initial = ser.readline().decode('utf-8').strip()
print(f"Initial: {initial}")

def send_command_and_speak(command_dict):
    text = command_dict.get("text", "")
    rate = engine.getProperty('rate')
    duration = calculate_duration(text, rate) if text.strip() else 0
    mouth_speed = command_dict.get("mouth_speed", 0.7)

    json_command = json.dumps(
        {
            "emotion": command_dict.get("emotion", "talking"),
            "talking_emotion": command_dict.get("talking_emotion", "neutral"),
            "text": text,
            "mouth_speed": mouth_speed,
            "duration": duration if duration > 0 else command_dict.get("duration", 1.0),
            "intensity": command_dict.get("intensity", 1.0),
            "volume": command_dict.get("volume", 1.0)
        },
        ensure_ascii=False
    )

    ser.write((json_command + "\r\n").encode('utf-8'))
    print(f"Sent: {json_command}")

    if text.strip():
        print(f"[TTS]: {text}")
        engine.say(text)
        engine.runAndWait()

    try:
        response = ser.readline().decode('utf-8').strip()
        print(f"Response: {response}")
    except Exception as e:
        print(f"[ERROR] Reading response: {e}")

# Первый запуск
initial_command = {
    "emotion": "talking",
    "text": "Скоро начнется турнир по Теккен 3 - 8! (и не только). Набирайте силы и приходите показать свои боевые навыки. Ждём всех, кто готов проиграть в поединках  Победителей ждут крутые призы и незабываемые эмоции особненно кто проиграет. Не упустите шанс стать чемпионом или проигравший! Если получиться победить Rendzhi King",
    "duration": 3,
    "mouth_speed": 0.9,
    "talking_emotion": "neutral"
}
send_command_and_speak(initial_command)

# Цикл команд
while True:
    try:
        print("Type 'q' to exit")
        command_input = input("> ").strip()
        if command_input.lower() == 'q':
            break

        try:
            parsed = json.loads(command_input)
            send_command_and_speak(parsed)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")

    except Exception as e:
        print(f"Error: {e}")

ser.close()
print("Connection closed")