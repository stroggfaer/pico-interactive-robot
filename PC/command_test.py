import serial
import time
import json
import pyttsx3

# Инициализация TTS
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if 'russian' in voice.name.lower() or 'irina' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break
engine.setProperty('rate', 150)


# Подключение к Pico через USB
PORT = 'COM5'
BAUDRATE = 115200
ser = serial.Serial(PORT, 921600, timeout=1)

time.sleep(2)


# Читаем начальное сообщение от Pico
initial = ser.readline().decode('utf-8').strip()
print(f"Initial: {initial}")

# Функция для отправки команды
def send_command(command_json):
    ser.write((command_json + "\r\n").encode('utf-8'))
    print(f"Sent: {command_json}")
    time.sleep(0.5)  # Даём время Pico обработать
    response = ser.readline().decode('utf-8').strip()
    print(f"Response: {response}")


initial_command = '{"emotion": "neutral", "text": "Под Лунным Деревом жила маленькая девочка по имени Лера. Под Лунным Деревом жила маленькая девочка по имени Лера."}'

send_command(initial_command)

# Цикл для ввода JSON-команд через терминал
while True:
    try:
        print("Type 'q' to exit")
        command_input = input("> ").strip()
        
        if command_input.lower() == 'q':
            break
        
        # Проверяем, что ввели валидный JSON
        try:
            json.loads(command_input)  # Проверка синтаксиса
            send_command(command_input)
           # time.sleep(2)  # Даём время увидеть результат (можно настроить)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
    
    except Exception as e:
        print(f"Error: {e}")

ser.close()
print("Connection closed")