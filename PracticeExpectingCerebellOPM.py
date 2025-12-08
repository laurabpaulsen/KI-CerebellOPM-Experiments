"""

"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.params import connectors

from ExpectingCerebellOPM import (
    ExpectationExperiment, VALID_INTENSITIES, STIM_DURATION, MAX_RESPONSE_TIME, create_trigger_mapping
)

def get_start_intensities() -> float:
    print("Please enter the starting intensity for the salient stimulus.")

    while True:
        try:
            salient = float(input("Enter intensity (1.0–10.0): "))
            if salient not in VALID_INTENSITIES:
                raise ValueError
            break
        except ValueError:
            print("❌ Invalid input. Please enter a number between 1.0 and 10.0 in steps of 0.1.")

    print("\nParticipant Information:")

    print(f" Intensity: {salient}")

    confirm = input("Is this information correct? (y/n): ").strip().lower()
    if confirm != "y":
        print("Exiting experiment setup.")
        exit()

    return salient



if __name__ in "__main__":

    print("This is for running the practice rounds of the EXPECTATION experiment.\n")
    intensity = get_start_intensities()

    for finger, connector in connectors.items():
        connector.set_pulse_duration(STIM_DURATION)
        connector.change_intensity(intensity)

    trigger_mapping = create_trigger_mapping()

    experiment = ExpectationExperiment(
        ISI=0.54,
        trigger_mapping=trigger_mapping,
        behavioural_task="second",
        connectors=connectors,
        n_events_per_block = 8,
        rng_interval =  (1, 1.5),
        n_repeats_per_block = 1,
        max_response_time=MAX_RESPONSE_TIME,
        outpath=None
    )
    
    experiment.run()