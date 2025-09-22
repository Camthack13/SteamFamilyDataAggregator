from __future__ import annotations
import threading
import time
import random
from typing import Callable

class HostGate:
    def __init__(self, base_delay: float = 0.8):
        self.base_delay = base_delay
        self._lock = threading.Lock()
        self._next_time = 0.0

    def wait(self):
        with self._lock:
            now = time.time()
            if now < self._next_time:
                time.sleep(self._next_time - now)
            # schedule next
            jitter = random.uniform(0.05, 0.2)
            self._next_time = time.time() + self.base_delay + jitter


def backoff_request(fn: Callable[[], 'requests.Response'], max_retries: int = 5):
    delay = 1.0
    for attempt in range(max_retries):
        resp = fn()
        if resp.status_code < 400 or resp.status_code == 404:
            return resp
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(delay + random.uniform(0, 0.5))
            delay = min(delay * 2, 60)
            continue
        return resp
    return resp