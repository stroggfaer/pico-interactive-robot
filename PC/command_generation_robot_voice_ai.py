import torch
from TTS.api import TTS
from torch.serialization import add_safe_globals
from TTS.tts.configs.xtts_config import XttsConfig, XttsAudioConfig
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.models.xtts import XttsArgs
import numpy as np
import scipy.io.wavfile as wavfile
import os

# Добавляем нужные классы в безопасный список
add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

# Убедимся что папка есть
os.makedirs("robot_voice", exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Используемое устройство: {device}")

try:
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)

    output_path = "robot_voice/output.wav"

    tts.tts_to_file(
        text="Внима-а-ние, бойцы-ы ретро-о-геймеры-ы!",
        file_path=output_path,
        speaker_wav="robot_voice/voice.mp3",
        language="ru"
    )
    print(f"Аудиофайл успешно создан: {output_path}")

    # === ДОБАВЛЯЕМ РОБО-ЭФФЕКТ ===
    sample_rate, data = wavfile.read(output_path)

    t = np.linspace(0, len(data) / sample_rate, num=len(data))
    modulator = np.sin(2 * np.pi * 70 * t)
    robotized = (data * modulator).astype(np.int16)

    robot_output_path = "robot_voice/output_robot.wav"
    wavfile.write(robot_output_path, sample_rate, robotized)

    print(f"Робо-аудио готово: {robot_output_path}")

except Exception as e:
    print(f"Произошла ошибка: {e}")
