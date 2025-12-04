import threading
import time
from typing import Dict, Optional, Tuple

import nidaqmx
from nidaqmx.constants import LineGrouping


class NIResponsePad:
    """
    Simple listener for 4-button response pad on NI PCIe-6509.
    Returns mapped labels to plug in easily to experiment code (e.g. "1","2","y","b").
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
        """
        Parameters
        ----------
        device, port, lines: used to form strings like "Dev1/port0/line0,..."
        mapping: dict mapping line index -> label returned to experiment (e.g. {0:"2",1:"1",2:"y",3:"b"})
                 if None, default returns str(index) ("0","1","2","3")
        poll_interval_s: how often to poll input lines (seconds)
        debounce_ms: ignore additional presses on the same line within this ms window
        timestamp_responses: if True, get_response() returns (label, timestamp)
        """
        self.device = device
        self.port = port
        self.lines = lines
        self.poll_interval_s = poll_interval_s
        self.debounce_s = debounce_ms / 1000.0
        self.mapping = mapping or {i: str(i) for i in range(len(lines))}
        self.timestamp_responses = timestamp_responses

        self.active = False           # mirrors your KeyboardListener usage
        self._task = None
        self._thread = None
        self._lock = threading.Lock()
        self._last_press_label: Optional[str] = None
        self._last_press_time: Optional[float] = None
        self._last_line_time = {i: 0.0 for i in range(len(lines))}
        print(f"NIResponsePad initialized on {self.device}/{self.port} lines {self.lines}")

    def _make_line_string(self) -> str:
        return ",".join([f"{self.device}/{self.port}/{ln}" for ln in self.lines])

    def _poll_loop(self):
        read = self._task.read
        while self.active:
            # read returns list of booleans (one per line)
            try:
                vals = read()
            except Exception:
                # if the task fails for any reason, stop polling
                break

            tnow = time.perf_counter()
            for idx, v in enumerate(vals):
                if v:
                    # debounce check per line
                    if (tnow - self._last_line_time.get(idx, 0.0)) >= self.debounce_s:
                        label = self.mapping.get(idx, str(idx))
                        with self._lock:
                            self._last_press_label = label
                            self._last_press_time = tnow
                        self._last_line_time[idx] = tnow
                        # we break so we capture the first active line per poll cycle (adjust if needed)
                        break
            time.sleep(self.poll_interval_s)

    def start_listener(self):
        """Create NI task and start polling thread."""
        if self._task is not None:
            return

        line_string = self._make_line_string()
        self._task = nidaqmx.Task()
        # CHAN_PER_LINE returns one boolean per line in order
        self._task.di_channels.add_di_chan(line_string, line_grouping=LineGrouping.CHAN_PER_LINE)

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
        """
        Returns:
          - If timestamp_responses False: label string or None
          - If timestamp_responses True: (label, timestamp) or None
        """
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