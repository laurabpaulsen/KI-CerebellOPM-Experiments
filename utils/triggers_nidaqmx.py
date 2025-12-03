"""
Description: Trigger interface using NI-DAQmx instead of parallel port.
"""

# -*- coding: utf-8 -*-

import nidaqmx
import time


# ---- CONFIGURE THIS ----
CHANNEL = "Dev1/port5/line0:7"   # all 8 bits on port 5
PULSE_WIDTH = 0.005             # 5 ms trigger
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


def setParallelData(code: int):
    """
    Send an 8-bit trigger code via NI-DAQmx.
    """
    if trigger_task is None:
        print(f"TRIG {code} (Fake — NI device not initialised)")
        return

    # Convert integer code → list of 8 bits
    bits = [(code >> i) & 1 for i in range(8)]

    # Pulse out
    trigger_task.write(bits, auto_start=True)
    time.sleep(PULSE_WIDTH)
    trigger_task.write([0] * 8, auto_start=True)


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
