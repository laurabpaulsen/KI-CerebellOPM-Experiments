"""
Description: Trigger interface using NI-DAQmx instead of parallel port.
"""

# -*- coding: utf-8 -*-

import time
import platform

USE_NIDAQ = platform.system() == "Windows"

if USE_NIDAQ:
    import nidaqmx
    from nidaqmx.constants import LineGrouping


# ---- CONFIGURE THIS ----
CHANNEL_OPM = "Dev1/port9/line0:7"   # All 8 lines of port 9
CHANNEL_SQUID = "Dev1/port0/line0:7"  # All 8 lines of port 0
PULSE_WIDTH = 0.02 # seconds (20 ms)
# -------------------------


_trigger_task_OPM = None
_trigger_task_SQUID = None


def _init_task():
    global _trigger_task_OPM
    global _trigger_task_SQUID

    if _trigger_task_OPM is not None and _trigger_task_SQUID is not None:
        return

    if USE_NIDAQ:
        _trigger_task_OPM = nidaqmx.Task(new_task_name="OPM Trigger Task")
        _trigger_task_OPM.do_channels.add_do_chan(
            CHANNEL_OPM,
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
        )
        print(f"[NI] Trigger task initialised on {CHANNEL_OPM} for OPM.")

        _trigger_task_SQUID = nidaqmx.Task(new_task_name="SQUID Trigger Task")
        _trigger_task_SQUID.do_channels.add_do_chan(
            CHANNEL_SQUID,
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
        )
        print(f"[NI] Trigger task initialised on {CHANNEL_SQUID} for SQUID.")
    else:
        print("[MOCK] NI-DAQ not available — using fake triggers.")
        _trigger_task_OPM = "MOCK"
        _trigger_task_SQUID = "MOCK"

        
def setParallelData(code=1):
    _init_task()

    if USE_NIDAQ:
        for task in [_trigger_task_OPM, _trigger_task_SQUID]:
            task.write(code, auto_start=True)  # Set lines to desired code without starting yet 
        time.sleep(PULSE_WIDTH)

        for task in [_trigger_task_OPM, _trigger_task_SQUID]:
            task.write(0, auto_start=True)  # Reset lines to 0 after pulse width
    else:
        # Fake trigger behaviour
        timestamp = time.perf_counter()
        print(f"[MOCK TRIGGER] {timestamp:.6f}  CODE={code}")
        time.sleep(PULSE_WIDTH)


def close_tasks():
    global _trigger_task_OPM
    global _trigger_task_SQUID

    if USE_NIDAQ:
        if _trigger_task_OPM is not None:
            _trigger_task_OPM.close()
            _trigger_task_OPM = None
            print("[NI] OPM trigger task closed.")
        if _trigger_task_SQUID is not None:
            _trigger_task_SQUID.close()
            _trigger_task_SQUID = None
            print("[NI] SQUID trigger task closed.")