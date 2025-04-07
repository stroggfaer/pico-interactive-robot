import machine
import tft_config
import time
import utime

from colors import STYLE_FACE, STYLE_FACE_RED, STYLE_EYE, STYLE_MOUTH
from mrx import *
from states import get_neutral_state, get_talking_state, get_anim_state  # Импортируем из states.py

# Инициализация дисплея
display = tft_config.config(2)  # Вертикальная ориентация
display.inversion_mode(False)
display.backlight.value(1)  # Включаем подсветку

STYLE_BG = 0x0000  # Чёрный фон
STYLE_FACE = 0xFFFF  # Чёрный фон
STYLE_MOUTH = 0xF800  # Красный рот 0xF800
STYLE_EYE = 0xFFFF   # Белый для глаз (если понадобится позже)

# Константы для экрана и стилей
WIDTH = 320
HEIGHT = 240

# Константы для масштабирования лица
PIXEL_SIZE = 20
MATRIX_WIDTH = 12 * PIXEL_SIZE   # 300 пикселей
MATRIX_HEIGHT = 12 * PIXEL_SIZE  # 300 пикселей
X_OFFSET = (WIDTH - MATRIX_WIDTH) // 2 - 43  # Смещение влево на 40
Y_OFFSET = 0  # Начало с верха, так как 300 > 240

VOWELS = "аеёиоуыэюяaeiouy"  # Гласные буквы для определения ритма речи
         
# Универсальная функция отрисовки матрицы
prev_matrix = None

def draw_matrix(matrix, pixel_size=PIXEL_SIZE, force_redraw=False):
    global prev_matrix
    
    # Если требуется принудительный сброс или prev_matrix еще не инициализирована
    if force_redraw or prev_matrix is None:
        display.fill(STYLE_BG)  # Полная очистка экрана
        prev_matrix = [[0] * len(matrix[0]) for _ in range(len(matrix))]  # Инициализация prev_matrix
    
    # Отрисовка только измененных пикселей
    for row in range(len(matrix)):
        for col in range(len(matrix[row])):
            if matrix[row][col] != prev_matrix[row][col]:
                x = X_OFFSET + col * pixel_size
                y = Y_OFFSET + row * pixel_size
                color = STYLE_FACE if matrix[row][col] == 1 else STYLE_BG
                display.fill_rect(x, y, pixel_size, pixel_size, color)
    
    # Обновляем prev_matrix копией текущей матрицы
    prev_matrix = [row[:] for row in matrix]
    
    
def count_syllables(text):
    """Подсчет слогов без использования re (регулярных выражений)."""
    count = 0
    for char in text:
        if char.lower() in VOWELS:
            count += 1
    return count or 1  # Минимум 1 слог, чтобы избежать деления на 0    
    
def talking_logic(state, text, speed=0.5, mouth_speed=0.1, open_mouth_matrix=None, closed_mouth_matrix=None, neutral_matrix=None):
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
        print(f"[DEBUG] Начало разговора: '{text}'")

    if state.get("talking", False):
        speech_duration = state["syllables"] * 120  # 120 мс на слог
        elapsed_time = utime.ticks_diff(current_time, state["start_time"])

        if elapsed_time < speech_duration:
            frame_duration = (speech_duration // state["syllables"]) * mouth_speed  
            if utime.ticks_diff(current_time, state["last_frame"]) >= frame_duration:
                state["frame"] = (state["frame"] + 1) % 2
                matrix = open_mouth_matrix if state["frame"] == 0 else closed_mouth_matrix
                draw_matrix(matrix)
                state["last_frame"] = utime.ticks_ms()
            utime.sleep_ms(10)
        else:
            state["talking"] = False
            draw_matrix(neutral_matrix)
            print(f"[DEBUG] Завершение разговора: '{text}'")
    else:
        draw_matrix(neutral_matrix)
        utime.sleep_ms(int(speed * 100))

    return state    

def anime_logic(
    state, speed=0.5,
    duration=2.0,
    matrix_start=None,
    matrix_anim_a=None,
    matrix_anim_b=None,
    matrix_anim_c=None, 
    matrix_end=None):
    """
    Универсальная функция анимации мимики
    
    Аргументы:
    - state: словарь состояния анимации
    - speed: базовая скорость анимации (секунды между кадрами)
    - duration: общая продолжительность анимации в секундах
    - matrix_start: начальная матрица
    - matrix_anim_a: первый кадр анимации
    - matrix_anim_b: второй кадр анимации
    - matrix_anim_c: третий кадр анимации
    - matrix_end: конечная матрица
    Возвращает: обновленное состояние
    """
    current_time = time.time()

    # Инициализация состояния
    if not state.get("animating", False) and duration > 0:
        state["animating"] = True
        state["start_time"] = current_time
        state["last_frame"] = current_time
        state["frame"] = 0
        state["cycle_count"] = 0
        # Проверка на правильность matrix_start перед использованием
        if matrix_start:
            draw_matrix(matrix_start)
        
        print(f"[DEBUG] +++Starting animation with duration {duration} speed: {speed}")
    
    if not state.get("animating", False) and duration <= 2:
       if matrix_start:
          draw_matrix(matrix_start)
          return state
          
    # Основной цикл анимации
    if state.get("animating", False) and duration > 2:
        elapsed_time = current_time - state["start_time"]
        
        if elapsed_time < duration:
            # Рассчитываем время одного кадра (4 кадра: start -> a -> b -> c -> start)
            frame_duration = speed  # Теперь скорость контролирует время между кадрами
            
            if current_time - state["last_frame"] >= frame_duration:
                state["frame"] = (state["frame"] + 1) % 4
                state["cycle_count"] = elapsed_time // (frame_duration * 2)
                
                # Определяем текущую матрицу в зависимости от кадра
                if state["frame"] == 0 and matrix_start is not None:
                    draw_matrix(matrix_start)
                elif state["frame"] == 1 and matrix_anim_a is not None:
                    draw_matrix(matrix_anim_a)
                elif state["frame"] == 2 and matrix_anim_b is not None:
                    draw_matrix(matrix_anim_b)
                elif state["frame"] == 3 and matrix_anim_c is not None:
                    draw_matrix(matrix_anim_c)
                
                state["last_frame"] = current_time
                print(f"[DEBUG] Frame: {state['frame']}, Cycle: {state['cycle_count']}")
        else:
            # Завершение анимации
            #state["animating"] = False
            draw_matrix(matrix_end)
            print("[DEBUG] Animation completed")
            time.sleep(1)
            return state
        
    return state

# Эмоция "angry_talking_pixel" с управляемым состояние
def angry_talking_pixel(speed=0.5, state=None, text=None, mouth_speed=1.0):
    if state is None:
        state = get_talking_state()
    
    # Используем универсальную функцию talking_logic
    state = talking_logic(
        state=state,
        text=text,
        speed=speed,
        mouth_speed=mouth_speed,
        open_mouth_matrix=ANGRY_OPEN_MOUTH,
        closed_mouth_matrix=ANGRY_CLOSED_MOUTH,
        neutral_matrix=ANGRY_CLOSED
    )
    
    return state

#Влюблен поцелуй анимаций
def smile_love_pixel(speed=0.5, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    
    state = anime_logic(
       state=state,
       speed=speed,
       duration=duration,
       matrix_start=SMILE_LOVE,
       matrix_anim_a=SMILE_LOVE_A,
       matrix_anim_b=SMILE_LOVE_B,
       matrix_anim_c=SMILE_LOVE_A,
       matrix_end=SMILE 
    )
    
    return state


def neutral(speed=0.2, state=None):
    # Инициализация состояния, если оно не передано или некорректно
    if state is None:
        state = get_neutral_state()
    
    # Инициализация начального времени, если оно еще не задано
    if state["start_time"] == 0:
        state["start_time"] = time.ticks_ms()
        state["last_blink"] = time.ticks_ms()
        state["last_yawn"] = time.ticks_ms()  # Инициализируем last_yawn
    
    current_time = time.ticks_ms()
    
    # Проверка на режим сна (30 секунд бездействия)
    if time.ticks_diff(current_time, state["start_time"]) >= 30000 and state["sleep_start"] is None:
        state["sleep_start"] = current_time
        state["sleep_blink_phase"] = 0  # Сбрасываем фазу анимации сна
        print("[DEBUG] Entering sleep mode")
    
    # Режим сна с чередованием NEUTRAL_SLEEP и NEUTRAL_BLINK
    if state["sleep_start"] is not None:
        elapsed_sleep = time.ticks_diff(current_time, state["sleep_start"])
        
        # Плавное чередование: 0.5 сек NEUTRAL_SLEEP, 0.2 сек NEUTRAL_BLINK
        sleep_cycle = elapsed_sleep % 700  # Цикл длится 0.7 сек (500 + 200 мс)
        if sleep_cycle < 500:  # 0.5 сек показываем NEUTRAL_SLEEP
            draw_matrix(NEUTRAL_SLEEP, force_redraw=state["matrix"])
            state["sleep_blink_phase"] = 0
        else:  # 0.2 сек показываем NEUTRAL_BLINK
            draw_matrix(NEUTRAL_BLINK, force_redraw=state["matrix"])
            state["sleep_blink_phase"] = 1
        
        time.sleep(0.1)  # Уменьшаем задержку для плавности в цикле сна
        
        # Выход из сна через 15 секунд
        if elapsed_sleep >= 15000:
            state["sleep_start"] = None
            state["start_time"] = current_time
            state["last_yawn"] = current_time  # Сбрасываем зевание при выходе из сна
            print("[DEBUG] Exiting sleep mode")
        return state
    
    # Проверка на моргание (случайный интервал 8-15 секунд)
    blink_interval = 8000 + (hash(str(current_time)) % 7000)  # 8-15 секунд
    if time.ticks_diff(current_time, state["last_blink"]) >= blink_interval:
        if state.get("blink_phase", 0) == 0:
            state["blink_phase"] = 1
            state["blink_start"] = current_time
            state["last_blink"] = current_time
            print("[DEBUG] Starting blink animation")
    
    # Управление фазами моргания
    if state.get("blink_phase", 0) > 0:
        elapsed = time.ticks_diff(current_time, state["blink_start"])
        if elapsed < 100:  # Начало моргания (полузакрытые глаза)
            draw_matrix(NEUTRAL_HALF_BLINK, force_redraw=state["matrix"])
        elif elapsed < 200:  # Полное моргание
            draw_matrix(NEUTRAL_BLINK, force_redraw=state["matrix"])
            state["blink_phase"] = 2
        elif elapsed < 300:  # Конец моргания (полузакрытые глаза)
            draw_matrix(NEUTRAL_HALF_BLINK, force_redraw=state["matrix"])
            state["blink_phase"] = 3
        else:  # Завершение моргания
            draw_matrix(NEUTRAL_NO_BLINK, force_redraw=state["matrix"])
            state["blink_phase"] = 0
            state["blink_start"] = None
            print("[DEBUG] Blink completed")
    else:
        # Зевание (каждые 20 секунд после 10 секунд работы)
        if time.ticks_diff(current_time, state["start_time"]) >= 10000 and \
           time.ticks_diff(current_time, state["last_yawn"]) >= 20000:
            # Плавная анимация зевания
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
            
    if state["matrix"] == True:
       state["matrix"] = False
       
    time.sleep(speed)
    return state  # Возвращаем state для сохранения состояния

#Смущеный
def embarrassed_pixel(speed=0.5, state=None, text=None, mouth_speed=1.0):
    if state is None:
        state = get_anim_state()
        
    draw_matrix(EMBARRASSED)
    return state


#Смех анимаций
def smile_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    
    state = anime_logic(
        state=state,speed=speed,
        duration=duration,
        matrix_start=SMILE_B,
        matrix_anim_a=SMILE_A,
        matrix_anim_b=SMILE_B,
        matrix_anim_c=SMILE_A,
        matrix_end=SMILE)
    return state

#Cтрашный
def scary_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    
    state = anime_logic(
        state=state,speed=speed,
        duration=duration,
        matrix_start=SCARY_B,
        matrix_anim_a=SCARY_C,
        matrix_anim_b=SCARY_D,
        matrix_anim_c=SCARY_C,
        matrix_end=SCARY_A)
    return state
#Радость
def happy_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
    
    state = anime_logic(
        state=state,speed=speed,
        duration=duration,
        matrix_start=SMILE,
        matrix_anim_a=SMILE_A,
        matrix_anim_b=SMILE,
        matrix_anim_c=HAPPY,
        matrix_end=HAPPY)
    return state

#Грутсный
def sad_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
        
    state = anime_logic(
      state=state,speed=speed,
      duration=duration,
      matrix_start=SAD_A,
      matrix_anim_a=SAD_A,
      matrix_anim_b=SAD,
      matrix_anim_c=SAD,
      matrix_end=SAD_A)
    return state
#Удивленый
def surprise_pixel(speed=0.3, state=None, duration=5.0):
    if state is None:
        state = get_anim_state()
        
    state = anime_logic(
      state=state,speed=speed,
      duration=duration,
      matrix_start=NEUTRAL_NO_BLINK,
      matrix_anim_a=SURPRISE,
      matrix_anim_b=SURPRISE,
      matrix_anim_c=SURPRISE,
      matrix_end=NEUTRAL_NO_BLINK)
    return state

# Режим разговора
def talking_pixel(speed=0.5, state=None, text=None, mouth_speed=0.5, emotion = 'neutral'):
    if state is None:
        state = get_talking_state()
    # Используем универсальную функцию talking_logic
    state = talking_logic(
        state=state,
        text=text,
        speed=speed,
        mouth_speed=mouth_speed,
        open_mouth_matrix=TALKING_A,
        closed_mouth_matrix=TALKING_B,
        neutral_matrix=NEUTRAL_NO_BLINK
    )
    print(f"[DEBUG] Talking pixel speed: {speed} mouth_speed: {mouth_speed}")
    return state