"""

"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from ExpectingCerebellOPM import ExpectationExperiment, create_trigger_mapping

from utils.params import (
    TARGET_1, TARGET_1_KEYS,
    TARGET_2, TARGET_2_KEYS,
    STIM_DURATION,  RNG_INTERVAL, ISI, VALID_INTENSITIES,
    connectors
)

from PracticeBreathingCerebellOPM import get_start_intensities, key_color_mapping


# Show practice instructions
practice_instructions = [
        "In this part of the experiment, you will feel tactile stimuli on your index and middle fingers.",
        "You will be presented with two stimuli in quick succession, and your task is to identify whether \nthe second stimulus was on your index finger or middle finger.",
    
        "The first stimulus is predictive of what finger will receive the second stimulus.",

        "However, sometimes the second stimulus will be on the other finger than expected.",

        "Indicate which finger received the second stimulus by pressing the corresponding key. \n\n\n"
        f"{TARGET_1} finger: {key_color_mapping[TARGET_1_KEYS[0]]} \n\n"
        f"{TARGET_2} finger: {key_color_mapping[TARGET_2_KEYS[0]]}\n\n"
        "Always use your right index finger to press the corresponding key.",

        "Respond as quickly and accurately as possible",
        
        "If you are unsure which finger received the target, make your best guess. \nThis experiment will not continue until you respond.",
    ]



def update_intensity():
    new_salient = None
    while True:
        update = input("\nUpdate salient intensity? (y/n): ").strip().lower()
        if "n" in update:
            break
        if "y" not in update:
            print("❌ Invalid input. Please enter 'y' or 'n'.")
            continue

        while True:
            try:
                new_salient = float(input("Enter new salient intensity (1.0–10.0): "))
                if new_salient not in VALID_INTENSITIES:
                    raise ValueError
                return new_salient
            except ValueError:
                print("❌ Invalid input. Enter a number between 1.0 and 10.0 in steps of 0.1.")

    return None


if __name__ == "__main__":

    print("This is for running the practice rounds of the EXPECTATION experiment.\n")
    intensity = get_start_intensities(return_weak=False)["salient"]

    for finger, connector in connectors.items():
        connector.set_pulse_duration(STIM_DURATION)
        connector.change_intensity(intensity)

    trigger_mapping = create_trigger_mapping()

    experiment = ExpectationExperiment(
        ISI=ISI,
        trigger_mapping=trigger_mapping,
        connectors=connectors,
        n_events_per_block=4,
        rng_interval=RNG_INTERVAL,
        n_repeats_per_block=1,
        prop_expected_unexpected=[0.5, 0.5], 
        outpath=None,
        practise_mode=True,
        send_trigger=False
    )
    
    experiment.display.show_instructions(practice_instructions)

    experiment.run()

    # check whether to update intensity and run short confirmation block
    new_salient = update_intensity()

    while new_salient is not None:
        intensity = new_salient

        for connector in connectors.values():
            connector.change_intensity(new_salient)
        #experiment.n_events_per_block = 2  # for a short confirmation block with 1 expected and 1 unexpected trial per condition
        experiment.blocks = [experiment.blocks[0]]  # use only the first two blocks for confirmation
        experiment.run()

        # n_events_per_block=6 for a short confirmation block with 1 expected and 1 unexpected trial per condition
        new_salient = update_intensity()


    print(f"Practice complete, final salient intensity: {intensity}.")