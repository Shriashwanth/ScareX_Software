import os
import wave
import time
import struct
import numpy as np
import logging
from pathlib import Path

try:
    from ScareX.config import config
except ImportError:
    from config import config

logger = logging.getLogger("ScareX.MockAudio")

class MockAudioGenerator:
    """
    Synthetic Mock Audio Generator for Software Pipeline Testing.
    Generates synthetic WAV audio for the 6 bird species and non-bird categories (motorcycle, speech, weather, etc.).
    All files are stored in data/mock_audio/ and tagged as non-authentic test data.
    """
    def __init__(self):
        self.output_dir = Path(config.mock_audio_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.display_names = config.DISPLAY_NAMES

    def generate_mock_audio(self, target_class="crow", duration_sec=3.0, sample_rate=22050, mock_conf=0.90):
        """
        Generate synthetic WAV file.
        Returns:
            dict: {
                'file_path': str,
                'species': str,
                'display_name': str,
                'duration_sec': float,
                'sample_rate': int,
                'confidence': float,
                'is_mock': True,
                'is_bird': bool,
                'is_motorcycle': bool,
                'badge': 'MOCK AUDIO — SYNTHETIC TEST DATA',
                'warning': 'Synthetic audio is for software testing only and is not a real bird recording.'
            }
        """
        duration = float(duration_sec)
        sr = int(sample_rate)
        num_samples = int(sr * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)

        audio_signal = self._synthesize_signal(target_class, t, sr, duration)

        # Normalize audio to prevent clipping
        max_val = np.max(np.abs(audio_signal))
        if max_val > 0:
            audio_signal = audio_signal / max_val * 0.85

        # Save to WAV file
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        filename = f"mock_{target_class}_{timestamp_str}.wav"
        file_path = self.output_dir / filename

        self._save_wav(file_path, audio_signal, sr)
        logger.info(f"[MockAudio] Generated synthetic WAV: {file_path}")

        is_bird = target_class in ["house_sparrow", "common_myna", "crow", "parrot", "pigeon", "peacock"]
        is_motorcycle = target_class in ["motorcycle_engine", "motorcycle"]

        disp_name = self.display_names.get(target_class, target_class.replace("_", " ").title())

        return {
            "file_path": str(file_path),
            "species": target_class,
            "display_name": disp_name,
            "duration_sec": duration,
            "sample_rate": sr,
            "confidence": float(mock_conf),
            "is_mock": True,
            "is_bird": is_bird,
            "is_motorcycle": is_motorcycle,
            "badge": "MOCK AUDIO — SYNTHETIC TEST DATA",
            "warning": "Synthetic audio is for software testing only and is not a real bird recording."
        }

    def _synthesize_signal(self, target_class, t, sr, duration):
        signal = np.zeros_like(t)

        if target_class == "house_sparrow":
            # High-frequency rapid chirps (3500-4500 Hz)
            chirp_rate = 4.0  # 4 chirps per sec
            for i in range(int(duration * chirp_rate)):
                t_start = i / chirp_rate
                mask = (t >= t_start) & (t < t_start + 0.12)
                t_sub = t[mask] - t_start
                freq_sweep = np.linspace(3500, 4800, len(t_sub))
                signal[mask] = np.sin(2 * np.pi * freq_sweep * t_sub) * np.exp(-t_sub * 20)

        elif target_class == "common_myna":
            # Dual-tone whistles (2000 & 3200 Hz)
            whistle_rate = 2.0
            for i in range(int(duration * whistle_rate)):
                t_start = i / whistle_rate
                mask = (t >= t_start) & (t < t_start + 0.25)
                t_sub = t[mask] - t_start
                tone1 = np.sin(2 * np.pi * 2200 * t_sub)
                tone2 = np.sin(2 * np.pi * 3200 * t_sub)
                signal[mask] = (tone1 + tone2) * 0.5 * np.sin(np.pi * t_sub / 0.25)

        elif target_class == "crow":
            # Harsh caw (700 Hz saw-wave + 1400 Hz harmonic, amplitude modulated at 15 Hz)
            caw_rate = 1.0
            for i in range(int(duration * caw_rate)):
                t_start = i / caw_rate
                mask = (t >= t_start) & (t < t_start + 0.5)
                t_sub = t[mask] - t_start
                base = np.sin(2 * np.pi * 750 * t_sub) + 0.5 * np.sin(2 * np.pi * 1500 * t_sub)
                mod = 0.5 + 0.5 * np.sin(2 * np.pi * 18 * t_sub)
                signal[mask] = base * mod * np.sin(np.pi * t_sub / 0.5)

        elif target_class == "parrot":
            # Squawking frequency sweep (2500 - 4200 Hz)
            squawk_rate = 1.5
            for i in range(int(duration * squawk_rate)):
                t_start = i / squawk_rate
                mask = (t >= t_start) & (t < t_start + 0.3)
                t_sub = t[mask] - t_start
                freq = 2500 + 1700 * np.sin(2 * np.pi * 4 * t_sub)
                signal[mask] = np.sin(2 * np.pi * freq * t_sub) * (1.0 - t_sub / 0.3)

        elif target_class == "pigeon":
            # Low coo (300 Hz sine wave with slow attack)
            coo_rate = 0.8
            for i in range(int(duration * coo_rate)):
                t_start = i / coo_rate
                mask = (t >= t_start) & (t < t_start + 0.6)
                t_sub = t[mask] - t_start
                signal[mask] = np.sin(2 * np.pi * 320 * t_sub) * np.sin(np.pi * t_sub / 0.6)**2

        elif target_class == "peacock":
            # High loud scream (1200 - 2800 Hz sweep)
            peacock_rate = 0.5
            for i in range(int(duration * peacock_rate)):
                t_start = i / peacock_rate
                mask = (t >= t_start) & (t < t_start + 1.2)
                t_sub = t[mask] - t_start
                freq = 1200 + 1600 * (t_sub / 1.2)
                signal[mask] = np.sin(2 * np.pi * freq * t_sub) * np.sin(np.pi * t_sub / 1.2)

        elif target_class in ["motorcycle_engine", "motorcycle", "car_engine", "tractor_engine"]:
            # Engine rumble: 80 - 220 Hz low frequency + sub-harmonics & cylinder pops
            base_freq = 110.0 if "motorcycle" in target_class else 140.0
            rumble = np.sin(2 * np.pi * base_freq * t) + 0.7 * np.sin(2 * np.pi * (base_freq * 2) * t) + 0.4 * np.sin(2 * np.pi * (base_freq * 0.5) * t)
            noise = np.random.normal(0, 0.2, len(t))
            # Throttle pulse modulation
            throttle = 0.7 + 0.3 * np.sin(2 * np.pi * 0.8 * t)
            signal = (rumble + noise) * throttle

        elif target_class in ["human_speech", "human_shouting"]:
            # Speech formant simulation
            formant1 = np.sin(2 * np.pi * 400 * t)
            formant2 = np.sin(2 * np.pi * 1200 * t)
            cadence = 0.5 + 0.5 * np.sin(2 * np.pi * 3.5 * t)
            signal = (formant1 + formant2) * cadence

        elif target_class == "dog_barking":
            bark_rate = 1.2
            for i in range(int(duration * bark_rate)):
                t_start = i / bark_rate
                mask = (t >= t_start) & (t < t_start + 0.2)
                t_sub = t[mask] - t_start
                bark_freq = 500 - 200 * (t_sub / 0.2)
                signal[mask] = np.sin(2 * np.pi * bark_freq * t_sub) * np.exp(-t_sub * 15)

        elif target_class in ["rain", "wind", "construction_noise", "machine_noise"]:
            # Filtered noise
            signal = np.random.normal(0, 0.4, len(t))

        else:
            # Low silence noise floor
            signal = np.random.normal(0, 0.002, len(t))

        return signal

    def _save_wav(self, file_path, audio_signal, sample_rate):
        int_signal = (audio_signal * 32767.0).astype(np.int16)
        with wave.open(str(file_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int_signal.tobytes())
