import irsdk
import yaml


class IRacingClient:
    def __init__(self):
        self.ir = irsdk.IRSDK()

    def connect(self) -> bool:
        return self.ir.startup()

    def disconnect(self):
        self.ir.shutdown()

    @property
    def is_connected(self) -> bool:
        return self.ir.is_initialized and self.ir.is_connected

    def update(self):
        self.ir.freeze_var_buffer_latest()

    def get(self, key) -> any:
        try:
            return self.ir[key]
        except KeyError:
            return None

    def get_yaml(self, key):
        raw = self.get(key)

        if isinstance(raw, dict):
            return raw

        try:
            return yaml.safe_load(raw) or {}
        except Exception:
            return {}
