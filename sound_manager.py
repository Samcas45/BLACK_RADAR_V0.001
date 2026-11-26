import os
import wave
import struct
import math
import random
from ursina import Audio
import config


class SoundManager:
    def __init__(self):
        self.sfx_dir = os.path.join("assets", "sfx")
        os.makedirs(self.sfx_dir, exist_ok=True)
        self._generate_all_sfx()

        self.sounds = {}
        self.ambient_rain = None
        self._load_audio_clips()

    def _write_wav(self, filename, samples, sample_rate=22050):
        filepath = os.path.join(self.sfx_dir, filename)
        if os.path.exists(filepath):
            return filepath
        with wave.open(filepath, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            packed = bytearray()
            for s in samples:
                clamped = max(-1.0, min(1.0, s))
                packed.extend(struct.pack("<h", int(clamped * 32767)))
            wav_file.writeframes(bytes(packed))
        return filepath

    def _generate_all_sfx(self):
        sr = 22050

        # 1. Pitido limpio de barrido de radar (1080 Hz con decaimiento)
        ping_samples = []
        for i in range(int(sr * 0.35)):
            t = i / sr
            env = math.exp(-t * 11.0)
            val = math.sin(2 * math.pi * 1080 * t) * 0.45 * env
            ping_samples.append(val)
        self._write_wav("radar_ping.wav", ping_samples, sr)

        # 2. Estática de radio aeronáutica
        static_samples = []
        for i in range(int(sr * 0.45)):
            t = i / sr
            env = math.sin(math.pi * (t / 0.45))
            noise = random.uniform(-0.35, 0.35)
            tone = math.sin(2 * math.pi * 1850 * t) * 0.08
            static_samples.append((noise + tone) * env)
        self._write_wav("radio_static.wav", static_samples, sr)

        # 3. Alarma de anomalía / fallo eléctrico
        alarm_samples = []
        for i in range(int(sr * 1.1)):
            t = i / sr
            freq = 520 if (int(t * 6) % 2 == 0) else 390
            env = min(1.0, t * 15) * math.exp(-t * 1.4)
            val = (math.sin(2 * math.pi * freq * t) * 0.4 + math.sin(2 * math.pi * 95 * t) * 0.3) * env
            alarm_samples.append(val)
        self._write_wav("alarm_anomaly.wav", alarm_samples, sr)

        # 4. Trueno / golpe grave atmosférico
        thunder_samples = []
        low_filter = 0.0
        for i in range(int(sr * 1.8)):
            t = i / sr
            env = math.exp(-t * 2.1)
            raw = random.uniform(-1.0, 1.0)
            low_filter = 0.92 * low_filter + 0.08 * raw
            thunder_samples.append(low_filter * 2.4 * env)
        self._write_wav("thunder.wav", thunder_samples, sr)

        # 5. Clic táctil de consola
        click_samples = []
        for i in range(int(sr * 0.06)):
            t = i / sr
            env = math.exp(-t * 65.0)
            click_samples.append(math.sin(2 * math.pi * 720 * t) * 0.35 * env)
        self._write_wav("ui_click.wav", click_samples, sr)

        # 6. Lluvia nocturna continua (loop 3.5s)
        rain_samples = []
        smooth = 0.0
        for i in range(int(sr * 3.5)):
            raw = random.uniform(-0.25, 0.25)
            smooth = 0.78 * smooth + 0.22 * raw
            rain_samples.append(smooth * 0.55)
        self._write_wav("rain_ambient.wav", rain_samples, sr)

    def _load_audio_clips(self):
        clip_names = ["radar_ping", "radio_static", "alarm_anomaly", "thunder", "ui_click"]
        for name in clip_names:
            try:
                path = f"assets/sfx/{name}.wav"
                self.sounds[name] = Audio(path, loop=False, autoplay=False, volume=config.settings["volume"])
            except Exception:
                self.sounds[name] = None

        try:
            self.ambient_rain = Audio(
                "assets/sfx/rain_ambient.wav",
                loop=True,
                autoplay=False,
                volume=config.settings["volume"] * 0.45
            )
        except Exception:
            self.ambient_rain = None

    def play(self, name, pitch=1.0):
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.volume = config.settings["volume"]
                snd.pitch = pitch
                snd.play()
            except Exception:
                pass

    def start_ambient(self):
        if self.ambient_rain and not self.ambient_rain.playing:
            try:
                self.ambient_rain.volume = config.settings["volume"] * 0.45
                self.ambient_rain.play()
            except Exception:
                pass

    def stop_ambient(self):
        if self.ambient_rain and self.ambient_rain.playing:
            try:
                self.ambient_rain.stop()
            except Exception:
                pass

    def update_volume(self):
        vol = config.settings["volume"]
        for snd in self.sounds.values():
            if snd:
                snd.volume = vol
        if self.ambient_rain:
            self.ambient_rain.volume = vol * 0.45