import random

NEUTRAL_STATE = {
        "last_blink": 0,
        "start_time": 0,
        "sleep_start": None,
        "last_yawn": None,
        "pupil_direction": random.randint(-3, 3),
        "blink": False,
        "blink_phase": 0,
        "blink_start": None,
        "matrix": True,
        "sleep_blink_phase": 0
}

TALKING_STATE = {
        "talking": False,
        "frame": 0,
        "start_time": 0,
        "last_frame": 0,
        "emotion": 'neutral',
        "syllables": 1
}

ANIM_STATE = {
        "animating": False,
        "frame": 0,
        "start_time": 0,
        "last_frame": 0,
        "cycle_count": 0
}

# Базовые состояния для эмоций
def get_neutral_state():
    return dict(NEUTRAL_STATE)

def get_talking_state():
    return dict(TALKING_STATE)

def get_anim_state():
    return dict(ANIM_STATE)

# Словарь начальных состояний для всех эмоций
INITIAL_STATES = {
    "neutral": get_neutral_state,        # Нейтральное выражение лица
    "smile": get_anim_state,             # Улыбка (анимация улыбки)
    "smile_love": get_anim_state,        # Улыбка с любовью (романтическая анимация)
    "embarrassed": get_anim_state,       # Смущение (анимация смущённого лица)
    "scary": get_anim_state,             # Страх (страшная анимация) #new
    "happy": get_anim_state,             # Радость (весёлая анимация) #new
    "sad": get_anim_state,               # Грусть (грустная анимация) #new
    "surprise": get_anim_state,          # Удивление (анимация удивлённого лица) #new
    "happy_circle": get_anim_state,      # Радостный круг (анимация с круговым движением) #new
    "talking": get_talking_state         # Разговор (стандартная анимация речи) #new
}

#Сбрось state
def reset_state(emotion):
    """Получить новое состояние для указанной эмоции"""
    return INITIAL_STATES.get(emotion, get_neutral_state)()
