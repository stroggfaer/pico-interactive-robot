import sys
import select
import machine
import st7789py as st7789
import tft_config
import time
import json
import random
import math
from machine import I2S, Pin
from states import reset_state, INITIAL_STATES
from emotions_pixel import *

# === Инициализация дисплея ===
try:
    tft = tft_config.config(2)
    tft.inversion_mode(False)
    print("[INFO] TFT initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize TFT: {e}")
    tft = None

# === Инициализация I2S для MAX98357 ===
try:
    audio_out = I2S(
        0,
        sck=Pin(16),
        ws=Pin(17),
        sd=Pin(18),
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO,
        rate=22050,
        ibuf=1000
    )
    print("✅ I2S успешно инициализирован!")
except Exception as e:
    print(f"⚠️ Ошибка I2S: {e}")
    audio_out = None

# === Глобальные переменные ===
current_emotion = "neutral"
current_duration = 6.0
current_intensity = 1.0
current_text = None
current_mouth_speed = 0.8
emotion_timer = 0
anim_duration = 15 

emotion_states = {
    name: reset_state(name)
    for name in [
        "neutral", "angry_talking", "smile", "smile_love", "embarrassed",
        "scary", "happy", "sad", "surprise", "talking"
    ]
}

emotions = {
    "neutral": lambda i: neutral(speed=0.2 * i, state=emotion_states["neutral"]),
    "angry_talking": lambda i: angry_talking_pixel(
        speed=current_intensity * i,
        state=emotion_states["angry_talking"],
        text=current_text,
        mouth_speed=current_mouth_speed,
        emotion='neutral'
    ) if tft else None,
    "smile": lambda i: smile_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["smile"],
        duration=anim_duration,
    ) if tft else None,
    "smile_love": lambda i: smile_love_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["smile_love"],
        duration=anim_duration,
    ) if tft else None,
    "embarrassed": lambda i: embarrassed_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["embarrassed"]
    ) if tft else None,
    "scary": lambda i: scary_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["scary"],
        duration=anim_duration,
    ) if tft else None,
    "happy": lambda i: happy_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["happy"],
        duration=anim_duration,
    ) if tft else None,
    "sad": lambda i: sad_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["happy"],
        duration=anim_duration,
    ) if tft else None,
    "surprise": lambda i: surprise_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["surprise"],
        duration=anim_duration,
    ) if tft else None,
    "talking": lambda i: talking_pixel(
        speed=current_intensity * i,
        state=emotion_states["talking"],
        text=current_text,
        mouth_speed=current_mouth_speed,
        emotion='neutral'
    ) if tft else None,
}

def play_tone(frequency, duration=0.15, volume=0.3):
    if not audio_out:
        print("⚠️ Audio not initialized!")
        return

    volume = max(0.0, min(1.0, volume))
    sample_rate = 22050
    num_samples = int(sample_rate * duration)
    audio_buffer = bytearray(num_samples * 2)

    for i in range(num_samples):
        fade = 1.0 - (i / num_samples)
        sample = int(32767 * volume * fade * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_buffer[i * 2] = sample & 0xFF
        audio_buffer[i * 2 + 1] = (sample >> 8) & 0xFF

    audio_out.write(audio_buffer)
    print(f"🎵 Played tone: {frequency} Hz, {duration} sec, volume: {volume}")

def reset_emotion_state(emotion):
    global emotion_timer
    emotion_states[emotion] = reset_state(emotion)
    emotion_timer = time.time()
    print(f"[DEBUG] Reset state for {emotion}")

def read_last_command():
    last = None
    while select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        if line:
            last = line
    return last

def main():
    global current_emotion, current_duration, current_intensity
    global current_text, current_mouth_speed, emotion_timer, anim_duration

    print("Pico started, waiting for JSON commands...")

    if tft:
        tft.fill(st7789.BLACK)
        reset_emotion_state(current_emotion)
        emotion_states[current_emotion] = emotions[current_emotion](current_intensity)

    while True:
        try:
            command_json = read_last_command()
            if command_json:
                print(f"Raw input: '{command_json}'")
                try:
                    command = json.loads(command_json)
                    new_emotion = command.get("emotion", "neutral")
                    current_duration = float(command.get("duration", 2.0))
                    current_intensity = float(command.get("intensity", 1.0))
                    current_mouth_speed = float(command.get("mouth_speed", 1.0))
                    current_text = command.get("text", None)
                    volume = float(command.get("volume", 0.3))
                    anim_duration = float(command.get("anim_duration", 5.0))
                    print(f"Parsed command: emotion={new_emotion}, duration={current_duration}, intensity={current_intensity}, text='{current_text}', mouth_speed={current_mouth_speed}")

                    if new_emotion != current_emotion or command.get("text") != current_text:
                        current_emotion = new_emotion
                        current_text = command.get("text", None)
                        reset_emotion_state(current_emotion)
                        if current_emotion not in emotions:
                            print(f"[ERROR] Emotion {current_emotion} not defined, defaulting to neutral")
                            current_emotion = "neutral"
                        if tft:
                            emotion_states[current_emotion] = emotions[current_emotion](current_intensity)

                except Exception as e:
                    print(f"⚠️ JSON parse error: {e}")

            if tft:
                emotion_states[current_emotion] = emotions[current_emotion](current_intensity)

                if ("talking" in emotion_states[current_emotion] and 
                    not emotion_states[current_emotion]["talking"] and 
                    current_text is not None):
                    current_text = None

            if time.time() - emotion_timer >= current_duration:
                if current_emotion != "neutral":
                    current_emotion = "neutral"
                    current_text = None
                    if tft:
                        reset_emotion_state(current_emotion)

            if ("animating" in emotion_states[current_emotion] and 
                not emotion_states[current_emotion]["animating"]):
                anim_duration = 0

            time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Main loop error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
