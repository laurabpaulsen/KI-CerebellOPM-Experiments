"""
Discriminating weak index and middle finger targets following three salient rhythm-establishing stimuli presented to both fingers
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.params import connectors
from utils.quest_controller import QuestController

from BreathingCerebellOPM import (
    MiddleIndexTactileDiscriminationTask, RESET_QUEST,
    STIM_DURATION, VALID_INTENSITIES, create_trigger_mapping,
    TARGET_1, TARGET_2, TARGET_1_KEYS, TARGET_2_KEYS
    )

key_color_mapping = {
    "1": "blue",
    "2": "yellow",
}

"""
def show_instructions(win, instructions: list[str], color="white"):

    Display instructions on a PsychoPy window.

    Parameters
    ----------
    win : psychopy.visual.Window
        The window to draw instructions on.
    instructions : list[str]
        Each string will be displayed on its own page.
    color : str
        Text color.
    key_to_continue : str
        The key the participant must press to continue to the next page.
    
    if not instructions:
        return
    
    for page in instructions:
        text_stim = visual.TextStim(
            win,
            text=page,
            color=color,
            wrapWidth=1.5,  # adjust to your window size
            height=0.05
        )
        text_stim.draw()
        win.flip()
        
        # Wait for participant key press
        input("Press any key to continue to the next page...")

"""
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
    practice_instructions = [
        "In this part of the experiment, you will feel tactile stimuli on your index and middle fingers.",
        
        "Your task is to identify whether the last stimulus in each sequence was on your index finger or middle finger.",
        
        "Each sequence begins with three rhythm-establishing stimuli. These are salient and presented to both fingers.",
        
        "During this time, the fixation cross will stay white.",
        
        "Next, a weaker target stimulus will be delivered to one finger only.",
        
        "When the target appears, the fixation cross will turn green.",

        "Indicate which finger received the target by pressing the corresponding key. \n\n\n"
        f"{TARGET_1} finger: {key_color_mapping[TARGET_1_KEYS[0]]} \n\n"
        f"{TARGET_2} finger: {key_color_mapping[TARGET_2_KEYS[0]]}",

        "Respond as quickly as possible, before the next sequence begins and the fixation cross turns white again.",
        
        "If you are unsure which finger received the target, make your best guess.",
    ]

    #for instruction in practice_instructions:
    #    show_instructions(win, [instruction])

    experiment.check_in_on_participant(message="Ready to begin practice block.")

    # clear the window before starting
    experiment.trial_block(ISI=1.5, n_sequences=6, debug=False)

    # possiblility to update intensities after first practice
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


    # practice but without the visual instructions (only with a white fixation cross)
    experiment.practice_mode = False
    experiment.check_in_on_participant(message="Ready to begin final practice block now without the green fixation cross to que response.")
    
    practice_instructions = [
        "In this final practice block, the fixation cross will remain white throughout the sequence.",
        "Please continue to indicate which finger received the target stimulus by pressing the corresponding key.",
        "Remember to respond as quickly as possible after the target stimulus.",
    ]
    #for instruction in practice_instructions:
    #    show_instructions(win, [instruction])

    experiment.trial_block(ISI=1.3, n_sequences=6)

  
