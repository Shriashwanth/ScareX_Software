import os
import json
import logging

class ScareXConfig:
    _instance = None
    _config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScareXConfig, cls).__new__(cls)
            cls._instance.config = cls._instance._load_defaults()
            cls._instance._load_file()
        return cls._instance

    def _load_defaults(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return {
            # System Settings
            "camera_index": 0,
            "flask_port": 5000,
            "dashboard_host": "0.0.0.0",
            "frame_width": 640,
            "frame_height": 480,
            "imgsz": 640,
            
            # Module A — Bird Detection & Deterrence Settings
            "vision_conf_threshold": 0.25,
            "audio_conf_threshold": 0.45,
            "iou_threshold": 0.45,
            "min_consecutive_detections": 1,
            "cooldown_sec": 0.0,
            "deterrence_duration_sec": 3.0,
            "max_repeat_triggers": 5,
            "manual_test_mode": False,
            "mute_mode": False,
            "emergency_stop": False,
            
            # Module B — Tomato Monitoring Settings
            "tomato_conf_threshold": 0.45,
            "harvest_ready_threshold": 0.40,      # >40% fully ripened -> Harvest Ready
            "ripening_stage_threshold": 0.35,     # >35% half ripened -> Ripening Stage
            "early_growth_threshold": 0.60,      # >60% green -> Early Growth
            "low_conf_warning_threshold": 0.40,  # <40% avg conf -> Monitoring Required
            "total_rows": 4,

            # Paths
            "vision_model_path": os.path.join(base_dir, "models", "best.pt"),
            "vision_ncnn_path": os.path.join(base_dir, "models", "best_ncnn_model"),
            "tomato_model_path": os.path.join(base_dir, "models", "tomato_model.pt"),
            "tomato_ncnn_path": os.path.join(base_dir, "models", "tomato_ncnn_model"),
            "audio_model_path": os.path.join(base_dir, "models", "audio_species_model.pth"),
            "sound_dir": os.path.join(base_dir, "sounds"),
            "db_path": os.path.join(base_dir, "data", "scarex.db"),
            "mock_audio_dir": os.path.join(base_dir, "data", "mock_audio"),
            "reports_dir": os.path.join(base_dir, "data", "reports"),
            "detections_dir": os.path.join(base_dir, "data", "detections")
        }

    def _load_file(self):
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                logging.error(f"[ScareXConfig] Error loading config.json: {e}")

    def save(self):
        try:
            with open(self._config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"[ScareXConfig] Error saving config.json: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def update(self, kwargs):
        for k, v in kwargs.items():
            if k in self.config:
                self.config[k] = v
        self.save()

    # Module A Species Mappings
    BIRD_SPECIES_MAP = {
        0: "house_sparrow",
        1: "common_myna",
        2: "crow",
        3: "parrot",
        4: "pigeon",
        5: "peacock"
    }

    # Module B Tomato Mappings
    TOMATO_CLASS_MAP = {
        0: "b_fully_ripened",
        1: "b_half_ripened",
        2: "b_green"
    }

    DISPLAY_NAMES = {
        "house_sparrow": "House Sparrow",
        "common_myna": "Common Myna",
        "crow": "Crow",
        "parrot": "Parrot",
        "pigeon": "Pigeon",
        "peacock": "Peacock",
        "unknown_bird": "Unknown Bird",
        "b_fully_ripened": "Fully Ripened",
        "b_half_ripened": "Half Ripened",
        "b_green": "Green",
        "non_bird_sound": "Non-bird Sound Detected",
        "motorcycle_engine": "Motorcycle Engine Sound",
        "unknown_sound": "Unknown Sound"
    }

    NON_BIRD_SOUND_CLASSES = [
        "motorcycle_engine", "car_engine", "truck_engine", "tractor_engine",
        "human_speech", "human_shouting", "dog_barking", "cat_sound",
        "rain", "wind", "thunder", "construction_noise", "machine_noise",
        "music", "silence", "unknown_environmental_sound"
    ]

    @property
    def bird_classes(self):
        return list(self.BIRD_SPECIES_MAP.values())

    @property
    def tomato_classes(self):
        return list(self.TOMATO_CLASS_MAP.values())

    @property
    def hardware_target(self):
        return "Raspberry Pi 5"

    def __getattr__(self, name):
        name_lower = name.lower()
        if name_lower in self.config:
            return self.config[name_lower]
        raise AttributeError(f"'ScareXConfig' object has no attribute '{name}'")

config = ScareXConfig()
