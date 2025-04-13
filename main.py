import sys
import select
import st7789py as st7789
import tft_config
import time
import json
import math
from machine import I2S, Pin
from states import reset_state, INITIAL_STATES
from emotions_pixel import *
import gc

try:
    tft = tft_config.config(2)
    tft.inversion_mode(False)
    print("[INFO] TFT initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize TFT: {e}")
    tft = None

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

current_emotion = "neutral" #neutral
talking_emotion = None #neutral angry
current_duration = 3.0
current_intensity = 1.0
current_text = None
current_mouth_speed = 0.5
emotion_timer = 0
anim_duration = 5


emotion_states = {
    name: reset_state(name)
    for name in [
        "neutral", "smile", "smile_love", "embarrassed",
        "scary", "happy", "sad", "surprise", "talking"
    ]
}

emotions = {
    "neutral": lambda i: neutral(speed=0.2 * i, state=emotion_states["neutral"]),
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
        state=emotion_states["sad"],
        duration=anim_duration,
    ) if tft else None,
    "surprise": lambda i: surprise_pixel(
        speed=current_mouth_speed * i,
        state=emotion_states["surprise"],
        duration=anim_duration,
    ) if tft else None,
    "talking": lambda i: talking_pixel(
        duration=current_duration,
        speed=current_intensity * i,
        state=emotion_states["talking"],
        text=current_text,
        mouth_speed=current_mouth_speed,
        emotion=talking_emotion
    ) if tft else None,
}

audio_buffer = bytearray(22050 * 2)

def play_tone(frequency, duration=0.15, volume=0.3):
    if not audio_out:
        print("⚠️ Audio not initialized!")
        return

    volume = max(0.0, min(1.0, volume))
    sample_rate = 22050
    num_samples = int(sample_rate * duration)

    for i in range(num_samples):
        fade = 1.0 - (i / num_samples)
        sample = int(32767 * volume * fade * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_buffer[i * 2] = sample & 0xFF
        audio_buffer[i * 2 + 1] = (sample >> 8) & 0xFF

    try:
        audio_out.write(audio_buffer[:num_samples * 2])
        print(f"🎵 Played tone: {frequency} Hz, {duration} sec, volume: {volume}")
    except Exception as e:
        print(f"⚠️ Audio write error: {e}")

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

def is_valid_command(command):
    return isinstance(command, dict) and "emotion" in command

last_emotion_time = time.time()

def main():
    global current_emotion, current_duration, current_intensity
    global current_text, current_mouth_speed, emotion_timer, anim_duration
    global last_emotion_time, talking_emotion
    #current_text = 'Не знаю, что сказать пока думаю или у меня мозги отключили'
    print("Pico started, waiting for JSON commands...")

    if tft:
        #tft.fill(st7789.BLACK)
        reset_emotion_state(current_emotion)
        emotions[current_emotion](current_intensity)

    new_command_received = False

    while True:
        try:
            command_json = read_last_command()
            if command_json:
                print(f"Raw input: '{command_json}'")
                try:
                    command = json.loads(command_json)

                    if not is_valid_command(command):
                        print("⚠️ Invalid command structure")
                        continue

                    new_emotion = command.get("emotion", "neutral")
                    current_duration = float(command.get("duration", 2.0))
                    current_intensity = float(command.get("intensity", 1.0))
                    current_mouth_speed = float(command.get("mouth_speed", 1.0))
                    current_text = command.get("text", None)
                    volume = float(command.get("volume", 0.3))
                    anim_duration = float(command.get("anim_duration", 5.0))
                    talking_emotion = command.get("talking_emotion", "neutral")

                    print(f"Parsed command: emotion={new_emotion},talking_emotion={talking_emotion}, duration={current_duration}, intensity={current_intensity}, text='{current_text}', mouth_speed={current_mouth_speed}")

                    if new_emotion not in emotions:
                        print(f"[ERROR] Emotion '{new_emotion}' not defined, using 'neutral'")
                        new_emotion = "neutral"

                    current_emotion = new_emotion
                    new_command_received = True

                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error: {e}")
                except Exception as e:
                    print(f"⚠️ Command parse error: {e}")
                finally:
                    gc.collect()

            if new_command_received and time.time() - last_emotion_time > 0.5:
                if tft:
                    reset_emotion_state(current_emotion)
                    emotions[current_emotion](current_intensity)
                    print(f"[SWITCH] Switching to {current_emotion}")
                last_emotion_time = time.time()
                new_command_received = False

            if tft:
                emotions[current_emotion](current_intensity)

                if not emotion_states[current_emotion].get("talking") and current_text is not None:
                    current_text = None
                    talking_emotion = None
                    gc.collect()

            if time.time() - emotion_timer >= current_duration:
                if current_emotion != "neutral":
                    current_emotion = "neutral"
                    current_text = None
                    talking_emotion = None
                    if tft:
                        reset_emotion_state(current_emotion)
                        emotions[current_emotion](current_intensity)
                        print("[TIMEOUT] Auto switch to neutral")
                    gc.collect()

            if not emotion_states[current_emotion].get("animating", True):
                anim_duration = 0

            time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Main loop error: {e}")
            time.sleep(1)
            gc.collect()

if __name__ == "__main__":
    main()

