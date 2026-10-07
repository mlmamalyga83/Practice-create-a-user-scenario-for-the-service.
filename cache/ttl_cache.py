import hashlib
import threading
import time


class TTLCache:
    def __init__(self, ttl: int = 600):
        self._ttl = ttl
        self._store: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def _make_key(self, message: str, model: str, temperature: float, system_prompt: str) -> str:
        raw = f"{message}|{model}|{temperature}|{system_prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, message: str, model: str, temperature: float, system_prompt: str):
        key = self._make_key(message, model, temperature, system_prompt)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, timestamp = entry
            elapsed = time.time() - timestamp
            if elapsed > self._ttl:
                del self._store[key]
                return None
            return value, self._ttl - elapsed

    def set(self, message: str, model: str, temperature: float, system_prompt: str, value: str):
        key = self._make_key(message, model, temperature, system_prompt)
        with self._lock:
            self._store[key] = (value, time.time())