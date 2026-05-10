import json
import os
from pathlib import Path


class ConfigLoader:
    _CONFIG_PATH = Path(__file__).parent.parent / "config" / "test_data.json"

    @classmethod
    def load(cls) -> dict:
        path = Path(os.environ.get("TEST_CONFIG_PATH", cls._CONFIG_PATH))
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
        cls._apply_env_overrides(config)
        return config

    @staticmethod
    def _apply_env_overrides(config: dict) -> None:
        """Allow ENV vars to override config values for CI/CD profiles."""
        if os.environ.get("HEADLESS"):
            config["headless"] = os.environ["HEADLESS"].lower() == "true"
        if os.environ.get("EBAY_USERNAME"):
            config["credentials"]["username"] = os.environ["EBAY_USERNAME"]
        if os.environ.get("EBAY_PASSWORD"):
            config["credentials"]["password"] = os.environ["EBAY_PASSWORD"]
        if os.environ.get("SLOW_MO"):
            config["slow_mo"] = int(os.environ["SLOW_MO"])
