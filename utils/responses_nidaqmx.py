import threading
import time
from typing import Dict, Optional, Union

import nidaqmx
from nidaqmx.constants import LineGrouping


class NIResponsePad:
    """
    Listener for a multi-line response pad on NI PCIe-6509.
    Supports edge detection and debounce for multiple successive presses.
    """

    def __init__(
        self,
        device: str = "Dev1",
        port: str = "port6",
        num_lines: int = 4,
        mapping: Union[Dict[int, str], None] = None,
        poll_interval_s: float = 0.0005,
        debounce_ms: int = 30,
        timestamp_responses: bool = False,
    ):
        self.device = device
        self.port = port
        self.num_lines = num_lines
        self.poll_interval_s = poll_interval_s
        self.debounce_s = debounce_ms / 1000.0
        self.timestamp_responses = timestamp_responses

        # Default mapping: 0 → "0", 1 → "1", etc.
        self.mapping = mapping or {i: str(i) for i in range(num_lines)}

        self.active = False
        self._task: Optional[nidaqmx.Task] = None
        self._thread: Optional[threading.Thread] = None

        self._lock = threading.Lock()
        self._last_press_label: Optional[str] = None
        self._last_press_time: Optional[float] = None
        self._last_line_time = {i: 0.0 for i in range(num_lines)}
        self._last_bits = [0] * num_lines  # track previous line states

        print(f"NIResponsePad initialized on {self.device}/{self.port} with {self.num_lines} lines")

    # ---------------------------------------------------------
    def _make_line_string(self):
        # e.g., "Dev1/port6/line0:3"
        return f"{self.device}/{self.port}/line0:{self.num_lines - 1}"

    # ---------------------------------------------------------
    def _poll_loop(self):
        # Cache the read method for performance
        read = self._task.read

        while self.active:
            try:
                raw_val = read()  # integer bitmask on PCIe-6509
            except Exception:
                break

            t = time.perf_counter()
            bits = [(raw_val >> i) & 1 for i in range(self.num_lines)]

            for idx, bit in enumerate(bits):
                # Rising edge detection
                if bit and self._last_bits[idx] == 0:
                    if (t - self._last_line_time[idx]) >= self.debounce_s:
                        label = self.mapping[idx]
                        with self._lock:
                            self._last_press_label = label
                            self._last_press_time = t
                        self._last_line_time[idx] = t

            self._last_bits = bits
            time.sleep(self.poll_interval_s)

    # ---------------------------------------------------------
    def start_listener(self):
        if self._task is not None:
            return

        line_string = self._make_line_string()
        self._task = nidaqmx.Task()
        self._task.di_channels.add_di_chan(
            line_string,
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
        )

        self.active = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    # ---------------------------------------------------------
    def stop_listener(self):
        self.active = False

        if self._thread:
            self._thread.join(timeout=0.1)
            self._thread = None

        if self._task:
            try:
                self._task.close()
            except Exception:
                pass
            self._task = None

    # ---------------------------------------------------------
    def get_response(self):
        """
        Returns:
          - If timestamp_responses is False: label string or None
          - If True: (label, timestamp) or None
        """
        with self._lock:
            label = self._last_press_label
            ts = self._last_press_time
            self._last_press_label = None
            self._last_press_time = None

        if label is None:
            return None
        if self.timestamp_responses:
            return (label, ts)
        return label
    
    def reset_response(self):
        """Clears any stored response without returning it."""
        with self._lock:
            self._last_press_label = None
            self._last_press_time = None
