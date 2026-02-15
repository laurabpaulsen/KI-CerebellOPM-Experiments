"""
Discriminating weak index and middle finger targets following three salient rhythm-establishing stimuli presented to both fingers
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.params import (
    STIM_DURATION, VALID_INTENSITIES, RESET_QUEST,
    TARGET_1, TARGET_2, TARGET_1_KEYS, TARGET_2_KEYS,
    connectors, 
)
from utils.quest_controller import QuestController

from BreathingCerebellOPM import MiddleIndexTactileDiscriminationTask, create_trigger_mapping

key_color_mapping = {
    "1": "blue",
    "2": "yellow",
}



def get_start_intensities(return_weak: bool = True):
    print("Please enter the starting intensities for BreathingCerebellum practice rounds.")

    while True:
        try:
            salient = float(input("Enter salient intensity (1.0–10.0): "))
            if salient not in VALID_INTENSITIES:
                raise ValueError
            break
        except ValueError:
            print("❌ Invalid input. Please enter a number between 1.0 and 10.0 in steps of 0.1.")

    weak = round(salient / 2, 1)
    print(f" Salient Intensity: {salient}\n")
    print(f" Weak Intensity: {weak}")

    confirm = input("Is this information correct? (y/n): ").strip().lower()
    if confirm != "y":
        print("Exiting setup.")
        exit()

    if return_weak:
        return {
            "salient": salient,
            "weak": weak
        }
    else:
        return {
            "salient": salient
        }
    

practice_instructions_1 = [
    "In this part of the experiment, you will feel electrical stimulations on your index and middle fingers.",
    
    "Each sequence begins with three rhythm-establishing stimuli. These are salient and presented to both fingers.",
    "During this time, the fixation cross will stay white.",    
    "Following these, a weaker target stimulus will be delivered to either your index or middle finger.",
        
    "When the target appears, the fixation cross will turn green.",

    "Indicate which finger received the target by pressing the corresponding key. \n\n\n"
    f"{TARGET_1} finger: {key_color_mapping[TARGET_1_KEYS[0]]} \n\n"
    f"{TARGET_2} finger: {key_color_mapping[TARGET_2_KEYS[0]]}\n\n"
    "Always use your right index finger to press the corresponding key.",

    "Respond as quickly as possible, before the next sequence begins and the fixation cross turns white again.",
        
    "If you are unsure which finger received the target, make your best guess.",
    "The stimulations will be weak, so it's normal to find it difficult to decide which finger received the target. \nJust try your best to respond based on what you feel.",
    ]

practice_instructions_2 = [
        "In this final practice block, the fixation cross will remain white throughout the sequence.",
        "Please continue to indicate which finger received the target stimulus by pressing the corresponding key.",
        "Remember to respond as quickly as possible after the target stimulus. \n\n Try to look at the fixation cross in the center of the screen throughout the experiment.",
    
    ]



def update_intensity(experiment):
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
                break
            except ValueError:
                print("❌ Invalid input. Enter a number between 1.0 and 10.0 in steps of 0.1.")

        # apply to experiment
        experiment.update_salient_intensity(new_salient)

        # short trial block to confirm
        experiment.check_in_on_participant(message="Ready to begin short confirmation block.")
        experiment.trial_block(ISI=1.3, n_sequences=4)

if __name__ == "__main__":
    # --- Collect participant info ---
    print("This is for running the practice rounds of the BREATHING experiment.\n")
    start_intensities = get_start_intensities()

    for finger, connector in connectors.items():
        connector.set_pulse_duration(STIM_DURATION)
        connector.change_intensity(start_intensities["salient"])

    quest_controller = QuestController(start_val=start_intensities["weak"], max_weak=start_intensities["salient"] - 0.3, target=0.75)

    experiment = MiddleIndexTactileDiscriminationTask(
        salient_intensity=start_intensities["salient"],
        n_sequences=1,
        order = [0],
        reset_QUEST=RESET_QUEST, # reset QUEST every x blocks
        ISIs=[1.5],
        trigger_mapping=create_trigger_mapping(),
        send_trigger=False,
        quest_controller=quest_controller,
        logfile = None,
        SGC_connectors=connectors,
        practice_mode=True,
    )

    # Show practice instructions
    experiment.display.show_instructions(practice_instructions_1)
    experiment.check_in_on_participant(message="Ready to begin practice block.")
    experiment.trial_block(ISI=1.5, n_sequences=6)

    # possiblility to update intensities after first practice
    update_intensity(experiment)

    # practice but without the visual instructions (only with a white fixation cross)
    experiment.practice_mode = False
    experiment.check_in_on_participant(message="Ready to begin final practice block now without the green fixation cross to que response.")
    
    
    experiment.display.show_instructions(practice_instructions_2)

    experiment.trial_block(ISI=1.3, n_sequences=6)

    # update intensities again if needed
    update_intensity(experiment)

  
