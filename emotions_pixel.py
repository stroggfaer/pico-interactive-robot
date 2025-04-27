import machine
import tft_config
import time
import utime

from colors import STYLE_FACE, STYLE_FACE_RED, STYLE_EYE, STYLE_MOUTH
from mrx import *
from states import get_neutral_state, get_talking_state, get_anim_state

# Инициализация дисплея
display = tft_config.config(2)
display.inversion_mode(False)
display.backlight.value(1)

STYLE_BG = 0x0000
STYLE_FACE = 0xFFFF
STYLE_MOUTH = 0xF800
STYLE_EYE = 0xFFFF

WIDTH = 320
HEIGHT = 240

PIXEL_SIZE = 20
MATRIX_WIDTH = 12 * PIXEL_SIZE
MATRIX_HEIGHT = 12 * PIXEL_SIZE
X_OFFSET = (WIDTH - MATRIX_WIDTH) // 2 - 43
Y_OFFSET = 0

VOWELS = "аеёиоуыэюяaeiouy"

prev_matrix = None

def reset_matrix():
    global prev_matrix
    prev_matrix = None

def draw_matrix(matrix, pixel_size=PIXEL_SIZE, force_redraw=False):
    global prev_matrix

    if force_redraw or prev_matrix is None:
        display.fill(STYLE_BG)
        prev_matrix = [[0] * len(matrix[0]) for _ in range(len(matrix))]

    for row in range(len(matrix)):
        for col in range(len(matrix[row])):
            if matrix[row][col] != prev_matrix[row][col]:
                x = X_OFFSET + col * pixel_size
                y = Y_OFFSET + row * pixel_size
                color = STYLE_FACE if matrix[row][col] == 1 else STYLE_BG
                display.fill_rect(x, y, pixel_size, pixel_size, color)

    prev_matrix = [row[:] for row in matrix]

def count_syllables(text):
    return sum(1 for char in text if char.lower() in VOWELS) or 1

def talking_logic(state, text, duration=1.0, speed=1.0, mouth_speed=1.0, open_mouth_matrix=None, closed_mouth_matrix=None, neutral_matrix=None):
    if open_mouth_matrix is None or closed_mouth_matrix is None:
        print("[ERROR] Required matrices for talking_logic are missing")
        return state

    current_time = utime.ticks_ms()

    if text and text.strip() and not state.get("talking", False):
        state["talking"] = True
        state["start_time"] = current_time
        state["last_frame"] = current_time
        state["frame"] = 0
        state["syllables"] = count_syllables(text)
        speech_duration = duration * 1500  # Переводим duration из секунд в миллисекунды
        reset_matrix()
        print(f"[DEBUG] Начало разговора: '{text}', duration: {speech_duration} ms")

    if state.get("talking", False):
        speech_duration = duration * 1500  # Используем переданный duration
        elapsed_time = utime.ticks_diff(current_time, state["start_time"])

        if elapsed_time < speech_duration:
            # Частота кадров: делим длительность на количество слогов
            frame_duration = (speech_duration // state["syllables"]) * mouth_speed
            if utime.ticks_diff(current_time, state["last_frame"]) >= frame_duration:
                state["frame"] = (state["frame"] + 1) % 2
                matrix = open_mouth_matrix if state["frame"] == 0 else closed_mouth_matrix
                draw_matrix(matrix)
                state["last_frame"] = utime.ticks_ms()
            utime.sleep_ms(10)
        else:
            state["talking"] = False
            reset_matrix()
            draw_matrix(neutral_matrix, force_redraw=True)
            print(f"[DEBUG] Завершение разговора: '{text}'")
    else:
        draw_matrix(neutral_matrix)
        utime.sleep_ms(int(speed * 100))

    return state


def anime_logic(state, speed=0.5, duration=2.0, matrix_start=None, matrix_anim_a=None, matrix_anim_b=None, matrix_anim_c=None, matrix_end=None):
    current_time = time.time()

    if not state.get("animating", False) and duration > 0:
        state["animating"] = True
        state["start_time"] = current_time
        state["last_frame"] = current_time
        state["frame"] = 0
        state["cycle_count"] = 0
        reset_matrix()
        if matrix_start:
            draw_matrix(matrix_start, force_redraw=True)
        print(f"[DEBUG] +++Starting animation with duration {duration} speed: {speed}")

    if not state.get("animating", False) and duration <= 2:
        if matrix_start:
            draw_matrix(matrix_start)
            return state

    if state.get("animating", False) and duration > 2:
        elapsed_time = current_time - state["start_time"]

        if elapsed_time < duration:
            frame_duration = speed

            if current_time - state["last_frame"] >= frame_duration:
                state["frame"] = (state["frame"] + 1) % 4
                state["cycle_count"] = elapsed_time // (frame_duration * 2)

                if state["frame"] == 0 and matrix_start:
                    draw_matrix(matrix_start)
                elif state["frame"] == 1 and matrix_anim_a:
                    draw_matrix(matrix_anim_a)
                elif state["frame"] == 2 and matrix_anim_b:
                    draw_matrix(matrix_anim_b)
                elif state["frame"] == 3 and matrix_anim_c:
                    draw_matrix(matrix_anim_c)

                state["last_frame"] = current_time
                print(f"[DEBUG] Frame: {state['frame']}, Cycle: {state['cycle_count']}")
        else:
            state["animating"] = False
            reset_matrix()
            draw_matrix(matrix_end, force_redraw=True)
            print("[DEBUG] Animation completed")
            time.sleep(1)

    return state

def smile_love_pixel(speed=0.5, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    return anime_logic(state, speed, duration, SMILE_LOVE, SMILE_LOVE_A, SMILE_LOVE_B, SMILE_LOVE_A, SMILE)

def neutral(speed=0.2, state=None):
    if state is None:
        state = get_neutral_state()

    if state["start_time"] == 0:
        state["start_time"] = time.ticks_ms()
        state["last_blink"] = time.ticks_ms()
        state["last_yawn"] = time.ticks_ms()

    current_time = time.ticks_ms()

    if time.ticks_diff(current_time, state["start_time"]) >= 30000 and state["sleep_start"] is None:
        state["sleep_start"] = current_time
        state["sleep_blink_phase"] = 0
        reset_matrix()
        print("[DEBUG] Entering sleep mode")

    if state["sleep_start"] is not None:
        elapsed_sleep = time.ticks_diff(current_time, state["sleep_start"])
        sleep_cycle = elapsed_sleep % 700
        if sleep_cycle < 500:
            draw_matrix(NEUTRAL_SLEEP, force_redraw=state["matrix"])
            state["sleep_blink_phase"] = 0
        else:
            draw_matrix(NEUTRAL_BLINK, force_redraw=state["matrix"])
            state["sleep_blink_phase"] = 1

        time.sleep(0.1)

        if elapsed_sleep >= 15000:
            state["sleep_start"] = None
            state["start_time"] = current_time
            state["last_yawn"] = current_time
            reset_matrix()
            print("[DEBUG] Exiting sleep mode")
        return state

    blink_interval = 8000 + (hash(str(current_time)) % 7000)
    if time.ticks_diff(current_time, state["last_blink"]) >= blink_interval:
        if state.get("blink_phase", 0) == 0:
            state["blink_phase"] = 1
            state["blink_start"] = current_time
            state["last_blink"] = current_time
            print("[DEBUG] Starting blink animation")

    if state.get("blink_phase", 0) > 0:
        elapsed = time.ticks_diff(current_time, state["blink_start"])
        if elapsed < 100:
            draw_matrix(NEUTRAL_HALF_BLINK, force_redraw=state["matrix"])
        elif elapsed < 200:
            draw_matrix(NEUTRAL_BLINK, force_redraw=state["matrix"])
            state["blink_phase"] = 2
        elif elapsed < 300:
            draw_matrix(NEUTRAL_HALF_BLINK, force_redraw=state["matrix"])
            state["blink_phase"] = 3
        else:
            draw_matrix(NEUTRAL_NO_BLINK, force_redraw=state["matrix"])
            state["blink_phase"] = 0
            state["blink_start"] = None
            print("[DEBUG] Blink completed")
    else:
        if time.ticks_diff(current_time, state["start_time"]) >= 10000 and time.ticks_diff(current_time, state["last_yawn"]) >= 20000:
            draw_matrix(NEUTRAL_NO_BLINK, force_redraw=state["matrix"])
            time.sleep(0.15)
            draw_matrix(NEUTRAL_HALF_BLINK, force_redraw=state["matrix"])
            time.sleep(0.15)
            draw_matrix(NEUTRAL_YAWN, force_redraw=state["matrix"])
            time.sleep(0.3)
            draw_matrix(NEUTRAL_HALF_BLINK, force_redraw=state["matrix"])
            time.sleep(0.15)
            draw_matrix(NEUTRAL_NO_BLINK, force_redraw=state["matrix"])
            state["last_yawn"] = current_time
            print("[DEBUG] Yawn completed")
        else:
            draw_matrix(NEUTRAL_NO_BLINK, force_redraw=state["matrix"])

    if state["matrix"]:
        state["matrix"] = False

    time.sleep(speed)
    return state

def embarrassed_pixel(speed=0.5, state=None, text=None, mouth_speed=1.0):
    if state is None:
        state = get_anim_state()
    reset_matrix()
    draw_matrix(EMBARRASSED, force_redraw=True)
    return state

def smile_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    return anime_logic(state, speed, duration, SMILE_B, SMILE_A, SMILE_B, SMILE_A, SMILE)

def scary_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    return anime_logic(state, speed, duration, SCARY_B, SCARY_C, SCARY_D, SCARY_C, SCARY_A)

def happy_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    return anime_logic(state, speed, duration, SMILE, SMILE_A, SMILE, HAPPY, HAPPY)

def sad_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    return anime_logic(state, speed, duration, SAD_A, SAD_A, SAD, SAD, SAD_A)

def surprise_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    return anime_logic(state, speed, duration, NEUTRAL_NO_BLINK, SURPRISE, SURPRISE, SURPRISE, NEUTRAL_NO_BLINK)

def talking_pixel(duration=1.0, speed=0.5, state=None, text=None, mouth_speed=0.5, emotion='neutral'):
    if state is None:
        state = get_talking_state() 
    if emotion == "neutral":
        return talking_logic(state, text, duration, speed, mouth_speed, TALKING_A, TALKING_B, NEUTRAL_NO_BLINK)
    elif emotion == "angry":
        return talking_logic(state, text, duration, speed, mouth_speed, ANGRY_OPEN_MOUTH, ANGRY_CLOSED_MOUTH, ANGRY_CLOSED)
    elif emotion == "smile_tricky":
        return talking_logic(state, text, duration, speed, mouth_speed, TALKING_TRICKY_A, TALKING_TRICKY_B, SMILE_A)
    elif emotion == "tricky":
        return talking_logic(state, text, duration, speed, mouth_speed, SMILE_TRICKY_A, SMILE_TRICKY_B, NEUTRAL_NO_BLINK)
    elif emotion == "smile":
        return talking_logic(state, text, duration, speed, mouth_speed, SMILE, TALKING_A, NEUTRAL_NO_BLINK)
    elif emotion == "ha":
        return talking_logic(state, text, duration, speed, mouth_speed, HAPPY_CIRCLE, NEUTRAL_CIRCLE, NEUTRAL_NO_BLINK)
    else:
        return talking_logic(state, text, duration, speed, mouth_speed, TALKING_A, TALKING_B, NEUTRAL_NO_BLINK)
