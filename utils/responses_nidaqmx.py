import threading
import time
from typing import Dict, Optional

import nidaqmx
from nidaqmx.constants import LineGrouping


class NIResponsePad:
    """
    4-button response pad listener for NI PCIe-6509.
    Uses line0:3 grouping and background polling thread.
    """

    def __init__(
        self,
        device: str = "Dev1",
        port: str = "port6",
        num_lines: int = 4,
        mapping: Dict[int, str] = None,
        poll_interval_s: float = 0.0005,
        debounce_ms: int = 50,
        timestamp_responses: bool = False,
    ):
        self.device = device
        self.port = port
        self.num_lines = num_lines
        self.poll_interval_s = poll_interval_s
        self.debounce_s = debounce_ms / 1000.0
        self.timestamp_responses = timestamp_responses

        self.mapping = mapping or {i: str(i) for i in range(num_lines)}

        # Internal state
        self.active = False
        self._task = None
        self._thread = None
        self._lock = threading.Lock()
        self._last_press_label = None
        self._last_press_time = None
        self._last_line_time = {i: 0.0 for i in range(num_lines)}

        print(f"NIResponsePad initialized on {device}/{port}, lines 0:{num_lines-1}")

    # ===================================================================

    def start_listener(self):
        """Start DAQ task and polling thread."""
        if self.active:
            return

        # Create task
        self._task = nidaqmx.Task()

        # Add lines in ONE channel: Dev1/port6/line0:3
        chan = f"{self.device}/{self.port}/line0:{self.num_lines-1}"

        self._task.di_channels.add_di_chan(
            chan,
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES,
        )

        print(f"NIResponsePad: Created DI channel {chan}")

        # Start polling thread
        self.active = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    # ===================================================================

    def _poll_loop(self):
        read = self._task.read

        while self.active:
            try:
                vals = read()  # returns list of booleans [L0, L1, L2, L3]
            except Exception as e:
                print("NIResponsePad ERROR during read():", e)
                break

            if not isinstance(vals, list) or len(vals) != self.num_lines:
                print("NIResponsePad ERROR: read() did not return expected list.")
                print("DEBUG read() output:", vals, type(vals))

                break

            tnow = time.perf_counter()

            # detect line activation
            for idx, pressed in enumerate(vals):
                if pressed:
                    # per-line debounce
                    if (tnow - self._last_line_time[idx]) >= self.debounce_s:
                        label = self.mapping.get(idx, str(idx))
                        with self._lock:
                            self._last_press_label = label
                            self._last_press_time = tnow
                        self._last_line_time[idx] = tnow
                        break

            time.sleep(self.poll_interval_s)

        print("NIResponsePad polling stopped.")

    # ===================================================================

    def get_response(self):
        """
        Returns:
            label (str)  – default
            (label, timestamp) – if timestamp_responses=True
        """
        with self._lock:
            label = self._last_press_label
            ts = self._last_press_time
            self._last_press_label = None
            self._last_press_time = None

        if label is None:
            return None

        return (label, ts) if self.timestamp_responses else label

    # ===================================================================

    def stop_listener(self):
        """Stops thread and closes DAQ task."""
        self.active = False

        if self._thread:
            self._thread.join(timeout=0.2)
            self._thread = None

        if self._task:
            try:
                self._task.close()
            except Exception:
                pass
            self._task = None

        print("NIResponsePad fully stopped.")
