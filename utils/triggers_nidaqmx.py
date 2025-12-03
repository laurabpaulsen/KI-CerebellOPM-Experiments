"""
Description: Trigger interface using NI-DAQmx instead of parallel port.
"""

# -*- coding: utf-8 -*-

import nidaqmx
import time


# ---- CONFIGURE THIS ----
CHANNEL = "Dev1/port9/line0:7"   # all 8 bits on port 5
PULSE_WIDTH = 0.01             # 10 ms trigger
# -------------------------


# Prepare task
try:
    trigger_task = nidaqmx.Task()
    trigger_task.do_channels.add_do_chan(CHANNEL)
    print(f"NI-DAQmx trigger task initialised on {CHANNEL}.")
except Exception as e:
    print("Could not initialise NI-DAQmx device:")
    print(e)
    trigger_task = None


def setParallelData(bits):
    """
    Send an 8-bit trigger code via NI-DAQmx.
    """
    if trigger_task is None:
        print(f"TRIG {bits} (Fake — NI device not initialised)")
        return

    # Pulse out
    trigger_task.write(bits, auto_start=True)
    time.sleep(PULSE_WIDTH)
    trigger_task.write([0] * 8, auto_start=True)


def create_trigger_mapping():

    trigger_mapping = {
        "stim/salient": [1, 0, 0, 0, 0, 0, 0, 0],
        "target/middle": [0, 1, 0, 0, 0, 0, 0, 0],
        "target/index": [0, 0, 1, 0, 0, 0, 0, 0],
        "response/index/correct": [0, 0, 0, 1, 1, 0, 0, 0],
        "response/middle/incorrect": [0, 0, 0, 0, 1, 1, 0, 0],
        "response/middle/correct": [0, 0, 0, 0, 1, 0, 1, 0],
        "response/index/incorrect": [0, 0, 0, 1, 0, 1, 0, 0],
        "break/start": [0, 0, 1, 1, 0, 0, 0, 0],
        "break/end": [0, 0, 0, 0, 1, 1, 1, 0],
        "experiment/start": [1, 1, 0, 0, 0, 0, 0, 0],
        "experiment/end": [0, 0, 0, 0, 0, 0, 0, 1],
        }

    return trigger_mapping
