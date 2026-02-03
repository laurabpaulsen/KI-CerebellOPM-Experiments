"""

"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.params import connectors

from ExpectingCerebellOPM import (
    ExpectationExperiment, STIM_DURATION, create_trigger_mapping, RNG_INTERVAL, ISI
)
from BreathingCerebellOPM import (
    TARGET_1, TARGET_1_KEYS,
    TARGET_2, TARGET_2_KEYS
    )

from PracticeBreathingCerebellOPM import get_start_intensities

key_color_mapping = {
    "1": "blue",
    "2": "yellow",

}

# Show practice instructions
practice_instructions = [
        "In this part of the experiment, you will feel tactile stimuli on your index and middle fingers.",
        
        "Your task is to identify whether the last stimulus in pair of stimuli was on your index finger or middle finger.",
        
        "The first stimulus somewhat predicts which finger will receive the second stimulus. \n\n\n." 
        "However, sometimes the second stimulus will be on the other finger than expected.",

        "Indicate which finger received the second stimulus by pressing the corresponding key. \n\n\n"
        f"{TARGET_1} finger: {key_color_mapping[TARGET_1_KEYS[0]]} \n\n"
        f"{TARGET_2} finger: {key_color_mapping[TARGET_2_KEYS[0]]}",

        "Respond as quickly and accurately as possible",
        
        "If you are unsure which finger received the target, make your best guess. This experiment will not continue until you respond.",
    ]


if __name__ in "__main__":

    print("This is for running the practice rounds of the EXPECTATION experiment.\n")
    intensity = get_start_intensities(return_weak=False)["salient"]

    for finger, connector in connectors.items():
        connector.set_pulse_duration(STIM_DURATION)
        connector.change_intensity(intensity)

    trigger_mapping = create_trigger_mapping()

    experiment = ExpectationExperiment(
        ISI=ISI,
        trigger_mapping=trigger_mapping,
        behavioural_task="second",
        connectors=connectors,
        n_events_per_block = 8,
        rng_interval =  RNG_INTERVAL,
        n_repeats_per_block = 10,
        prop_expected_unexpected=[0.5, 0.5], # no statistical regularities in practice
        outpath=None,
        practise_mode=True,
        send_trigger=False
    )
    
    experiment.run()