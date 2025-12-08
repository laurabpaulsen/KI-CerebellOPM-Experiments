"""
Discriminating weak index and middle finger targets following three salient rhythm-establishing stimuli presented to both fingers
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from typing import Union, List, Tuple, Optional
from collections import Counter
import random
from psychopy.core import wait
from psychopy.data import QuestPlusHandler, QuestHandler
from psychopy.clock import CountdownTimer
import time

import numpy as np

from utils.params import connectors 
from utils.triggers_nidaqmx import create_trigger_mapping, setParallelData

from utils.responses_nidaqmx import NIResponsePad

from BreathingCerebellOPM import (
    MiddleIndexTactileDiscriminationTask,get_participant_info, 
    ISIS, N_REPEATS_BLOCKS, 
    N_SEQUENCE_BLOCKS, RESET_QUEST,
    STIM_DURATION, VALID_INTENSITIES,
    generate_block_order
    )


if __name__ == "__main__":
    # --- Collect participant info ---
    print("This is for running the practice rounds of the BREATHING experiment.\n")
    participant_id, start_intensities = get_participant_info()


    for finger, connector in connectors.items():
        connector.set_pulse_duration(STIM_DURATION)
        connector.change_intensity(start_intensities["salient"])

    order = generate_block_order(ISIs=ISIS, n_repeats=N_REPEATS_BLOCKS)
    print(f"Block order: {order}")

    
    experiment = MiddleIndexTactileDiscriminationTask(
        intensities=start_intensities,
        n_sequences=N_SEQUENCE_BLOCKS,
        order = order,
        QUEST_plus=False,
        reset_QUEST=RESET_QUEST, # reset QUEST every x blocks
        ISIs=ISIS,
        trigger_mapping=create_trigger_mapping(),
        send_trigger=False,
        logfile = None,
        SGC_connectors=connectors,
        prop_target1_target2=[1/2, 1/2],
    )

    
    experiment.check_in_on_participant(message="Ready to begin practice block.")
    experiment.trial_block(ISI=1.5, n_sequences=12)

    # possiblility to update intensities after first practice
    while True:
        update = input("\nUpdate salient intensity? (y/n): ").strip().lower()
        if "y" not in update:
            break

        while True:
            try:
                new_salient = float(input("Enter new salient intensity (1.0–10.0): "))
                if new_salient not in VALID_INTENSITIES:
                    raise ValueError
                break
            except ValueError:
                print("❌ Invalid input. Enter a number between 1.0 and 10.0 in steps of 0.1.")

        # apply to experiment
        experiment.intensities["salient"] = new_salient

        # push new values to the devices
        for side, connector in experiment.SGC_connectors.items():
            connector.change_intensity(new_salient)

        # short trial block to confirm
        experiment.check_in_on_participant(message="Ready to begin short confirmation block.")
        experiment.trial_block(ISI=1.5, n_sequences=4)




