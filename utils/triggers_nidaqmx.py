"""
Description: Trigger interface using NI-DAQmx instead of parallel port.
"""

# -*- coding: utf-8 -*-

import nidaqmx
import time


# ---- CONFIGURE THIS ----
CHANNEL = "Dev1/port9/line0:7"   # All 8 lines of port 9
PULSE_WIDTH = 0.005 # seconds (5 ms)
# -------------------------


# Global task (initialized once)
_trigger_task = None


def _init_task():
    """Create the NI-DAQmx digital output task once."""
    global _trigger_task
    if _trigger_task is None:
        _trigger_task = nidaqmx.Task()
        _trigger_task.do_channels.add_do_chan(
            CHANNEL,
            line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES
        )
        print(f"NI-DAQmx trigger task initialised on {CHANNEL}.")


def setParallelData(code):
    """
    Send an 8-bit trigger vector via NI-DAQmx.
    bitlist example: [1,0,0,0,0,0,0,0]
    """
    _init_task()

    _trigger_task.write(code, auto_start=True)
    time.sleep(PULSE_WIDTH)

    # Back to zero
    _trigger_task.write([False] * 8, auto_start=True)



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