import threading
import time
from typing import Dict, Optional

import nidaqmx
from nidaqmx.constants import LineGrouping


class NIResponsePad:
    """
    Listener for a 4-button response pad on NI PCIe-6509.
    Handles integer bitmask input (the format returned by the 6509).
    """

    def __init__(
        self,
        device: str = "Dev1",
        port: str = "port6",
        lines: tuple = ("line0", "line1", "line2", "line3"),
        mapping: Dict[int, str] = None,
        poll_interval_s: float = 0.0005,
        debounce_ms: int = 30,
        timestamp_responses: bool = False,
    ):
        self.device = device
        self.port = port
        self.lines = lines
        self.num_lines = len(lines)
        self.poll_interval_s = poll_interval_s
        self.debounce_s = debounce_ms / 1000.0
        self.mapping = mapping or {i: str(i) for i in range(self.num_lines)}
        self.timestamp_responses = timestamp_responses

        self.active = False
        self._task = None
        self._thread = None

        self._lock = threading.Lock()
        self._last_press_label = None
        self._last_press_time = None
        self._last_line_time = {i: 0.0 for i in range(self.num_lines)}

        print(f"NIResponsePad initialized on {self.device}/{self.port}")

    def _make_line_string(self):
        # We use CHAN_FOR_ALL_LINES → DAQmx returns bitmask (integer)
        # Example: "Dev1/port6/line0:3"
        first = self.lines[0].replace("line", "")
        last = self.lines[-1].replace("line", "")
        return f"{self.device}/{self.port}/line{first}:{last}"

    def _poll_loop(self):
        read = self._task.read
        while self.active:
            try:
                value = read()  # <-- returns integer bitmask
            except Exception:
                break

            tnow = time.perf_counter()

            # Decode integer → list of booleans
            # bit0 = line0, bit1 = line1, ...
            bits = [(value >> i) & 1 for i in range(self.num_lines)]

            for idx, bit in enumerate(bits):
                if bit:
                    if (tnow - self._last_line_time[idx]) >= self.debounce_s:
                        label = self.mapping.get(idx, str(idx))
                        with self._lock:
                            self._last_press_label = label
                            self._last_press_time = tnow
                        self._last_line_time[idx] = tnow
                        break

            time.sleep(self.poll_interval_s)

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

    def get_response(self):
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
