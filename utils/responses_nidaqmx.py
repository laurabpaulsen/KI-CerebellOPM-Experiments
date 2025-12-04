import threading
import time
from typing import Dict, Optional, Tuple

import nidaqmx
from nidaqmx.constants import LineGrouping


class NIResponsePad:
    """
    Simple listener for 4-button response pad on NI PCIe-6509.
    Returns mapped labels to plug in easily to experiment code.
    """

    def __init__(
        self,
        device: str = "Dev1",
        port: str = "port6",
        lines: tuple = ("line0", "line1", "line2", "line3"),
        mapping: Dict[int, str] = None,
        poll_interval_s: float = 0.0005,
        debounce_ms: int = 50,
        timestamp_responses: bool = False,
    ):
        self.device = device
        self.port = port
        self.lines = lines
        self.poll_interval_s = poll_interval_s
        self.debounce_s = debounce_ms / 1000.0
        self.mapping = mapping or {i: str(i) for i in range(len(lines))}
        self.timestamp_responses = timestamp_responses

        self.active = False
        self._task = None
        self._thread = None
        self._lock = threading.Lock()
        self._last_press_label: Optional[str] = None
        self._last_press_time: Optional[float] = None
        self._last_line_time = {i: 0.0 for i in range(len(lines))}

        print(f"NIResponsePad initialized on {self.device}/{self.port} lines {self.lines}")

    def _poll_loop(self):
        while self.active:
            try:
                vals = self._task.read()  # should be list of booleans, one per line
            except Exception as e:
                print("NIResponsePad: read() failed:", e)
                break

            # If DAQmx returned a single value instead of a list
            if not isinstance(vals, list):
                print("NIResponsePad ERROR: read() did not return a list. Channel config is wrong.")
                break

            tnow = time.perf_counter()

            for idx, v in enumerate(vals):
                if v:
                    if (tnow - self._last_line_time.get(idx, 0)) >= self.debounce_s:
                        label = self.mapping.get(idx, str(idx))
                        with self._lock:
                            self._last_press_label = label
                            self._last_press_time = tnow
                        self._last_line_time[idx] = tnow
                        break

            time.sleep(self.poll_interval_s)

    def start_listener(self):
        """Create NI task and start polling thread."""
        if self._task is not None:
            return

        self._task = nidaqmx.Task()

        # --- FIXED: add each line as separate channel ---
        for ln in self.lines:
            ch_str = f"{self.device}/{self.port}/{ln}"
            self._task.di_channels.add_di_chan(
                ch_str, line_grouping=LineGrouping.CHAN_PER_LINE
            )

        print("NIResponsePad: Channels created =",
              len(self._task.di_channels))

        self.active = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_listener(self):
        """Stop polling and close the NI task."""
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

    def get_response(self) -> Optional[object]:
        with self._lock:
            label = self._last_press_label
            timestamp = self._last_press_time
            self._last_press_label = None
            self._last_press_time = None

        if label is None:
            return None
        if self.timestamp_responses:
            return (label, timestamp)
        return label
