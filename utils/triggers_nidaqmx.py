"""
Description: Trigger interface using NI-DAQmx instead of parallel port.
"""

# -*- coding: utf-8 -*-

import nidaqmx
import time


# ---- CONFIGURE THIS ----
CHANNEL = "Dev1/port9/line0:7"   # All 8 lines of port 9
PULSE_WIDTH = 0.1                # 100 ms trigger pulse
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


def create_trigger_mapping():
    """
    Return a dict mapping event names to 8-bit trigger lists.
    """
    return {
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
