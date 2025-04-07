from machine import I2S, Pin

class Audio:
    def __init__(self):
        """Инициализация I2S для MAX98357"""
        try:
            self.audio_out = I2S(
                0,                  # I2S ID
                sck=Pin(16),        # BCLK
                ws=Pin(17),         # LRCLK
                sd=Pin(18),         # DIN
                mode=I2S.TX,        # Передача
                bits=16,            # 16 бит на сэмпл
                format=I2S.STEREO,  # Стерео
                rate=44100,         # Частота 44.1 кГц
                ibuf=4000           # Буфер
            )
            print("I2S initialized successfully")
        except Exception as e:
            print(f"Failed to initialize I2S: {e}")
            self.audio_out = None

    def play(self, data):
        """Воспроизведение аудиоданных"""
        if self.audio_out and data:
            try:
                audio_buffer = bytes.fromhex(data)  # Предполагаем hex-строку
                self.audio_out.write(audio_buffer)
                print("Playing audio")
            except Exception as e:
                print(f"Audio playback error: {e}")

    def deinit(self):
        """Деинициализация I2S"""
        if self.audio_out:
            self.audio_out.deinit()
            print("I2S deinitialized")