# app/backend/proxy_scheduler.py
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.backend.models import ProxyItem
from app.backend.proxy_validator import validate_all_proxies, DEFAULT_TEST_URL, DEFAULT_THREADS as DEFAULT_VALIDATOR_THREADS

DEFAULT_SCHEDULER_INTERVAL = 3600
# Use the default from proxy_validator if not specified for ProxyScheduler
DEFAULT_PROXY_SCHEDULER_THREADS = DEFAULT_VALIDATOR_THREADS

class ProxyScheduler:
    def __init__(self,
                 initial_interval_seconds: int = DEFAULT_SCHEDULER_INTERVAL,
                 initial_validation_threads: int = DEFAULT_PROXY_SCHEDULER_THREADS,
                 test_url: str = DEFAULT_TEST_URL):
        self.interval_seconds: int = initial_interval_seconds
        self.validation_threads: int = initial_validation_threads
        self.test_url: str = test_url
        self._current_proxies: List[ProxyItem] = []
        self._last_run_time: Optional[datetime] = None
        self._next_run_time: Optional[datetime] = None
        self._status: str = "stopped"
        self._validation_in_progress: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._pause_event: threading.Event = threading.Event()
        self._refresh_event: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()
        self._pause_event.set()

    def _perform_validation(self):
        with self._lock:
            if self._validation_in_progress: return
            self._validation_in_progress = True
            self._status = "validating"
            self._last_run_time = datetime.now()
            current_threads_for_run = self.validation_threads

        print(f"[{datetime.now()}] SCHEDULER: Starting proxy validation with {current_threads_for_run} threads...")
        try:
            # validate_all_proxies now handles de-duplication of its input source (get_all_proxies)
            # and returns a list of updated ProxyItem objects.
            validated_proxies_list = validate_all_proxies(
                proxy_list_input=None, # Let it call get_all_proxies internally
                num_threads=current_threads_for_run,
                test_url=self.test_url
            )
            # The list from validate_all_proxies should now have is_valid, response_time correctly set.
            
            with self._lock:
                self._current_proxies = validated_proxies_list # Assign the processed list
                valid_count = sum(1 for p in self._current_proxies if p.is_valid)
                print(f"[{datetime.now()}] SCHEDULER: Validation finished. Stored {len(self._current_proxies)} proxies ({valid_count} valid).")
        except Exception as e:
            print(f"[{datetime.now()}] SCHEDULER: Error during proxy validation: {e}")
        finally:
            with self._lock:
                self._validation_in_progress = False
                self._status = "stopped" if self._stop_event.is_set() else ("paused" if self._pause_event.is_set() else "running")


    def _scheduler_loop(self):
        print(f"[{datetime.now()}] Scheduler loop started.")
        if not self._stop_event.is_set():
            self._perform_validation()

        while not self._stop_event.is_set():
            with self._lock:
                self._next_run_time = (self._last_run_time or datetime.now()) + timedelta(seconds=self.interval_seconds)
            
            wait_until = self._next_run_time
            while datetime.now() < wait_until and not self._stop_event.is_set():
                if self._refresh_event.is_set(): self._refresh_event.clear(); print(f"[{datetime.now()}] Refresh triggered."); break
                if self._pause_event.is_set():
                    with self._lock: self._status = "paused"
                    print(f"[{datetime.now()}] Scheduler paused."); self._pause_event.wait(); print(f"[{datetime.now()}] Scheduler resumed.")
                    with self._lock: self._status = "running" # Assume resume means running
                    break # Re-evaluate next run time or run immediately
                time.sleep(1)

            if self._stop_event.is_set(): break
            if not self._pause_event.is_set(): self._perform_validation()

        print(f"[{datetime.now()}] Scheduler loop stopped.")
        with self._lock: self._status = "stopped"; self._next_run_time = None

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                if self._pause_event.is_set(): self.resume()
                return
            print(f"Starting scheduler (threads: {self.validation_threads}, interval: {self.interval_seconds}s)...")
            self._stop_event.clear(); self._pause_event.clear()
            self._thread = threading.Thread(target=self._scheduler_loop, daemon=True); self._thread.start()
            self._status = "running"

    def stop(self):
        with self._lock:
            if not (self._thread and self._thread.is_alive()): self._status = "stopped"; return
            print("Stopping scheduler..."); self._stop_event.set(); self._pause_event.set(); self._refresh_event.set()
        if self._thread: self._thread.join(timeout=max(5, self.interval_seconds // 10)); # Shorter timeout for join
        with self._lock: self._thread = None; self._status = "stopped"; self._next_run_time = None
        print("Scheduler stopped.")

    def pause(self):
        with self._lock:
            if self._status not in ["running", "validating"]: return
            print("Pausing scheduler..."); self._pause_event.set()

    def resume(self):
        with self._lock:
            if self._status != "paused": return
            print("Resuming scheduler..."); self._pause_event.clear()

    def refresh_now(self, background: bool = True):
        with self._lock:
            if self._validation_in_progress: return "Validation already in progress."
            if self._status == "stopped": return "Scheduler stopped."
        if background or self._status == "paused":
            threading.Thread(target=self._perform_validation, daemon=True).start()
            return "Refresh task started in background."
        else: self._refresh_event.set(); return "Refresh signal sent."

    def set_interval(self, seconds: int):
        if seconds <= 0: return
        with self._lock: self.interval_seconds = seconds; print(f"Interval set to {seconds}s.")
        # Next run time will adjust in the loop

    def set_validation_threads(self, num_threads: int):
        if num_threads <= 0: return
        with self._lock: self.validation_threads = num_threads; print(f"Validation threads set to {num_threads}.")

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "validation_in_progress": self._validation_in_progress,
                "interval_seconds": self.interval_seconds,
                "validation_threads": self.validation_threads,
                "test_url": self.test_url,
                "last_run_time": self._last_run_time.isoformat() if self._last_run_time else None,
                "next_run_time": self._next_run_time.isoformat() if self._next_run_time else None,
                "current_proxy_count": len(self._current_proxies),
                "valid_proxy_count": sum(1 for p in self._current_proxies if p.is_valid),
            }

    def get_proxies(self, only_valid: bool = True) -> List[ProxyItem]:
        with self._lock:
            if only_valid: return [p for p in self._current_proxies if p.is_valid]
            return list(self._current_proxies)