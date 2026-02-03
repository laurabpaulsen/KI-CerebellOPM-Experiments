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
PULSE_WIDTH = 0.002 # seconds (5 ms)
# -------------------------


_trigger_task_OPM = None
_trigger_task_SQUID = None


def _init_task():
    global _trigger_task_OPM
    global _trigger_task_SQUID

    if _trigger_task_OPM is not None and _trigger_task_SQUID is not None:
        return

    if USE_NIDAQ:
        _trigger_task_OPM = nidaqmx.Task()
        _trigger_task_OPM.do_channels.add_do_chan(
            CHANNEL_OPM,
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
        )
        print(f"[NI] Trigger task initialised on {CHANNEL_OPM} for OPM.")

        _trigger_task_SQUID = nidaqmx.Task()
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
        _trigger_task_OPM.write(code, auto_start=True)
        _trigger_task_SQUID.write(code, auto_start=True) 
        time.sleep(PULSE_WIDTH)
        _trigger_task_OPM.write([False] * 8, auto_start=True)
        _trigger_task_SQUID.write([False] * 8, auto_start=True)
    else:
        # Fake trigger behaviour
        timestamp = time.perf_counter()
        print(f"[MOCK TRIGGER] {timestamp:.6f}  CODE={code}")
        time.sleep(PULSE_WIDTH)


def create_trigger_mapping(
        stim = 1,
        target = 2,
        middle = 4,
        index = 8,
        response = 16,
        correct = 32,
        incorrect = 64):
    
    trigger_mapping = {
        "stim/salient": stim,
        "target/middle": target + middle,
        "target/index": target + index,
        "response/index/correct": response + index + correct,
        "response/middle/incorrect": response + middle + incorrect,
        "response/middle/correct": response + middle + correct,
        "response/index/incorrect": response + index + incorrect,
        "break/start": 128,
        "break/end": 129,
        "experiment/start": 254,
        "experiment/end": 255
        }

    return trigger_mapping