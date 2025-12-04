"""
Discriminating weak index and middle finger targets following three salient rhythm-establishing stimuli presented to both fingers
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))

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



import os
if os.name != "posix":
    from winsound import PlaySound, SND_FILENAME
else:
    SND_FILENAME = None
    def PlaySound(*args, **kwargs):
        pass



# CONFIG
# -------------------
N_REPEATS_BLOCKS = 4 #4
N_SEQUENCE_BLOCKS = 8
RESET_QUEST = 2 # how many blocks before resetting QUEST
ISIS = [1.29, 1.44, 1.57, 1.71] 
VALID_INTENSITIES = np.arange(1.0, 10.1, 0.1).round(1).tolist()
STIM_DURATION = 100  # 0.1 ms

OUTPUT_PATH = Path(__file__).parent / "output"
OUTPUT_PATH.mkdir(exist_ok=True)



    
class MiddleIndexTactileDiscriminationTask:
    LOG_HEADER = "time,block,ISI,intensity,event_type,trigger,n_in_block,correct,QUEST_reset,rt\n"

    def __init__(
            self, 
            trigger_mapping: dict,
            ISIs: List[float],
            order: List[int],
            n_sequences: int = 10,
            prop_middle_index: List[float] = [0.5, 0.5],
            intensities: dict = {"salient": 6.0, "weak": 2.0},
            QUEST_target: float = 0.75,
            reset_QUEST: Union[int, bool] = False, # how many blocks before resetting QUEST
            QUEST_plus: bool = True,
            send_trigger: bool = False,
            logfile: Path = Path("data.csv"),
            SGC_connectors = None,
            break_sound_path=None,
            target_1="middle",
            target_2="index",
        ):
        
    
        """
        Initializes the parameters and attributes for the experimental paradigm.

        Parameters
        ----------
    
        order : list, optional
            The sequence order of stimuli types in the experiment, represented as 
            indices (0, 1, 2, etc.). Defaults to [0, 1, 0, 2, 1, 0, 2, 1, 0, 2, 0, 1].
        
        n_sequences : int, optional
            Number of sequences in each block. Defaults to 10.
        
        prop_target1_target2 : list, optional
            Proportions of target1 and target2.
            Defaults to [0.5, 0.5].
        
        intensities : dict, optional
            A dictionary mapping stimulus types ("salient", "weak") to intensity values.
            Defaults to {"salient": 4.0, "weak": 2.0}.
        
        trigger_mapping : dict, optional
            A mapping of stimulus and response types to specific trigger values sent
            during the experiment.
        
        QUEST_target : float, optional
            Target proportion of correct responses for QUEST to adjust intensity.
            Defaults to 0.75.
    
        
        reset_QUEST : int or bool, optional
            Determines if and how frequently the QUEST algorithm should reset.
            Set to an integer for resets every X blocks or False to disable resetting.
            Defaults to False.
        
        logfile : Path, optional
            Path to the log file for saving experimental data. Defaults to Path("data.csv").

        Returns
        -------
        None
        """
        
        self.ISIs = ISIs
        self.reset_QUEST = reset_QUEST
        self.logfile = logfile
        self.n_sequences = n_sequences
        self.order = order
        self.trigger_mapping = trigger_mapping
        self.prop_middle_index = prop_middle_index
        self.send_trigger = send_trigger
        self.SGC_connectors = SGC_connectors

        self.countdown_timer = CountdownTimer() 
        self.events = []
        
        self.target_1 = target_1
        self.target_2 = target_2

        # for response handling 
        self.listener = NIResponsePad(
            device="Dev1",
            port="port6",
            num_lines=4,
            mapping={
                0: 'b',  # right key
                1: 'y',  # left key
            },
            poll_interval_s=0.0005,
            debounce_ms=50,
            timestamp_responses=False
        )

        self.keys_target = {
            target_1: ['2', 'y'],
            target_2: ['1', 'b']
        }
        
        
        # QUEST parameters
        self.intensities =  intensities 
        self.QUEST_start_val = intensities["weak"] # NOTE: do we want to reset QUEST with the startvalue or start from a percentage of the weak intensity stimulation?
        self.max_intensity_weak = intensities["salient"] - 0.5
        self.QUEST_plus = QUEST_plus
        self.QUEST_target = QUEST_target 
        self.QUEST_n_resets = 0
        self.QUEST_reset()
        self.break_sound_path = break_sound_path



        self.start_time = time.perf_counter()

    def play_break_sound(self):
        # Play a sound to indicate a break
        if self.break_sound_path:
            PlaySound(str(self.break_sound_path), SND_FILENAME)

    def setup_experiment(self):
        logged_block_idx = 0
        for block_idx, block in enumerate(self.order):
            if block == "break":
                self.events.append("break")

            else:
                ISI = self.ISIs[block]

                # check if QUEST needs to be reset in this block
                if self.reset_QUEST and block_idx % self.reset_QUEST == 0 and block_idx != 0:
                    reset = int( self.n_sequences/2) # approximately halfway through the block
                else:
                    reset = False

                self.events.extend(self.event_sequence(self.n_sequences, ISI, logged_block_idx, reset_QUEST=reset))
                logged_block_idx += 1
        
    def event_sequence(self, n_sequences, ISI, block_idx, n_salient=3, reset_QUEST: Union[int, None] = None) -> List[dict]:
        """
        Generate a sequence of events for a block

        reset_QUEST: int or None
            If an integer, the QUEST procedure will be reset after this many sequences
        """
        event_counter_in_block = 0

        events = []
        for seq in range(n_sequences):
            
            # checking if it is time for a QUEST reset
            reset = reset_QUEST and seq == reset_QUEST

            for i in range(n_salient):
                event_counter_in_block += 1
                events.append({"ISI": ISI, "event_type": "stim/salient", "n_in_block": event_counter_in_block, "block": block_idx, "reset_QUEST": reset})
                if reset:
                    reset=False
            
            event_counter_in_block += 1
            event_type = np.random.choice([self.target_1, self.target_2], 1, p=self.prop_target1_target2)
            

            events.append({"ISI": ISI, "event_type": f"target/{event_type[0]}", "n_in_block": event_counter_in_block, "block": block_idx, "reset_QUEST": False})

        return events
    
    def make_QUEST_handler(self):
        if self.QUEST_plus:
            return QuestPlusHandler(
                startIntensity=self.QUEST_start_val,
                intensityVals=[round(i, 1) for i in np.arange(1.0, self.max_intensity_weak, 0.1)],
                thresholdVals=[round(i, 1) for i in np.arange(1.0, self.max_intensity_weak, 0.1)],
                stimScale="linear",
                responseVals=(1, 0),
                slopeVals=[3, 4, 5],
                lowerAsymptoteVals=0.5,
                lapseRateVals=0.05,
                nTrials=None
            )
        else:
            return QuestHandler(
                startVal=self.QUEST_start_val,
                startValSd=1.0,
                minVal=1.0,
                maxVal=self.max_intensity_weak,
                pThreshold=self.QUEST_target,
                stepType="linear",
                nTrials=None,
                beta=3.5,
                gamma=0.5,
                delta=0.01
            )
        
    
    def QUEST_reset(self):
        """Reset the QUEST procedure and update intensity."""

        # update the quest start val to the previous weak intensity
        if self.QUEST_n_resets > 0:
            self.QUEST_start_val = min(self.QUEST.mean(), self.max_intensity_weak)
            print(f"QUEST start value updated to: {self.QUEST_start_val}")
        self.QUEST = self.make_QUEST_handler()

        self.update_weak_intensity()
        self.QUEST_n_resets += 1
        print("QUEST has been reset")

    def update_weak_intensity(self):
        """
        Update the weak intensity based on the QUEST procedure!
        """
        proposed_intensity = self.QUEST.next()
    
        # make sure the intensity is not higher than the max allowed
        proposed_intensity = max(1.0, min(proposed_intensity, self.max_intensity_weak))

        self.intensities["weak"] = round(proposed_intensity, 1)

    def deliver_stimulus(self, event_type):
        raise NotImplementedError("Subclasses should implement this!")

    def prepare_for_next_stimulus(self, event_type, next_event_type):
        raise NotImplementedError("Subclasses should implement this!")
    
    def check_in_on_participant(self, message: str = "Check in on the participant.", log_file=None):
        if self.send_trigger:
            self.raise_and_lower_trigger(self.trigger_mapping["break/start"])
            # also log the event¨
            if log_file:
                self.log_event(
                    event_time=time.perf_counter() - self.start_time,
                    block="break",
                    ISI="NA",
                    intensity="NA",
                    event_type="break",
                    trigger=self.trigger_mapping["break/start"],
                    n_in_block="NA",
                    correct="NA",
                    reset_QUEST=False,
                    rt="NA",
                    log_file=log_file
                )

        #self.play_break_sound()
        input(message + " Press Enter to continue...")
        if self.send_trigger:
            self.raise_and_lower_trigger(self.trigger_mapping["break/end"])
            if log_file:
                self.log_event(
                    event_time=time.perf_counter() - self.start_time,
                    block="break",
                    ISI="NA",
                    intensity="NA",
                    event_type="break/end",
                    trigger=self.trigger_mapping["break/end"],
                    n_in_block="NA",
                    correct="NA",
                    reset_QUEST=False,
                    rt="NA",
                    log_file=log_file
                )
        wait(2)

    def loop_over_events(self, events: List[dict], log_file):
        """
        Loop over the events in the experiment
        """
        # how many breaks
        total_breaks = events.count("break")

        n_breaks_done = 0


        for i, trial in enumerate(events):
            if trial == "break":
                self.check_in_on_participant(log_file=log_file)
                n_breaks_done += 1
                continue
            
            event_type = trial["event_type"]
            trigger = self.trigger_mapping[event_type]

            intensity = self.intensities["salient"] if "salient" in event_type else self.intensities["weak"]

            if self.send_trigger:
                self.raise_and_lower_trigger(trigger)  # Send trigger
            
            # deliver pulse
            self.deliver_stimulus(event_type)
            print(f"Progress: {i+1}/{len(events)}, Breaks: {n_breaks_done}/{total_breaks}")

            stim_time = time.perf_counter() - self.start_time
            
            self.log_event(
                **trial,
                event_time=stim_time,
                intensity=intensity,
                trigger=trigger,
                log_file=log_file
            )
            
            print(f"Event: {event_type}, intensity: {intensity}")

            target_time = stim_time + trial["ISI"]
            response_given = False # to keep track of whether a response has been given

            try: 
                self.prepare_for_next_stimulus(event_type, events[i+1]["event_type"])
            except IndexError:
                pass
            except TypeError: # if break is coming up next
                try:
                    self.prepare_for_next_stimulus(event_type, events[i+2]["event_type"])
                except IndexError:
                    pass

            if trial["reset_QUEST"]:
                self.QUEST_reset()
            if "target" in event_type:
                self.listener.reset_response()
                response_given = False
            
            while (time.perf_counter() - self.start_time) < target_time:
                # check for key press during target window
                if "target" in event_type and not response_given:
                    rt = "NA"
                    key = self.listener.get_response()
                    if key:
                        correct, response_trigger = self.correct_or_incorrect(key, event_type)
                        time_of_response = (time.perf_counter() - self.start_time)

                        print(f"Response: {key}, Correct: {correct}")
                        if self.send_trigger:
                            self.raise_and_lower_trigger(response_trigger)

                        rt = time_of_response - stim_time
                        response_given = True
                            
                        # overwrite event type for logging
                        trial["event_type"] = "response"
                        if log_file:
                            self.log_event(
                                **trial,
                                event_time=time_of_response,
                                intensity="NA",
                                trigger=response_trigger,
                                correct=correct,
                                rt=rt,
                                log_file=log_file
                            )
                            

                        self.QUEST.addResponse(correct, intensity=intensity)
                        self.update_weak_intensity()

            if ("target" in event_type) and (not response_given):
                print("No response given")
                # Update QUEST with the guessed outcome and advance intensity
                self.QUEST.addResponse(np.random.choice([0, 1]), intensity=intensity)
                self.update_weak_intensity()




    def log_event(self, event_time="NA", block="NA", ISI="NA", intensity="NA", event_type="NA", trigger="NA", n_in_block="NA", correct="NA", reset_QUEST="NA", rt="NA", log_file=None):
        if log_file:
            log_file.write(f"{event_time},{block},{ISI},{intensity},{event_type},{trigger},{n_in_block},{correct},{reset_QUEST},{rt}\n")
    
    
    def get_user_input_respiratory_rate(self):
        while True:
            try:
                respiratory_rate = float(input("Please input the average length of one respiratory cycle: "))
                if respiratory_rate <= 0:
                    print("Invalid input. Please enter a positive value.")
                else: 
                    break
            except ValueError:
                print("Invalid input. Please enter a numeric value.")

        return respiratory_rate


    def correct_or_incorrect(self, key, event_type):
        if key in self.keys_target[event_type.split('/')[-1]]:
            return 1, self.trigger_mapping[f"response/{event_type.split('/')[-1]}/correct"]
        else:
            return 0, self.trigger_mapping[f"response/{event_type.split('/')[-1]}/incorrect"]


    def estimate_duration(self, break_duration: float = 30.0) -> float:
        """
        Estimate the total duration of the experiment in seconds.
        This calculation is based on the actual order of blocks (including breaks),
        the number of sequences per block, and the ISI structure.

        Parameters
        ----------
        break_duration : float
            Estimated duration of breaks in seconds.

        Returns
        -------
        float
            Estimated duration of the experiment in seconds.
        """
        total_duration = 0.0
        
        for block in self.order:
            if block == "break":
                # give an arbitrary pause duration for breaks (e.g. 60 s)
                total_duration += break_duration
                continue

            ISI = self.ISIs[block]
            n_events_per_sequence = 3 + 1  # 3 salient + 1 target per sequence
            n_events = n_events_per_sequence * self.n_sequences
            
            total_duration += n_events * ISI

        return total_duration
    

    def run(self, write_header: bool = True):
        self.listener.start_listener()  # Start the keyboard listener
        self.logfile.parent.mkdir(parents=True, exist_ok=True)  # Ensure log directory exists
       
        with open(self.logfile, 'w') as log_file:
            if write_header:
                log_file.write(self.LOG_HEADER)

            if self.send_trigger:
                self.raise_and_lower_trigger(self.trigger_mapping["experiment/start"])

            self.log_event(
                event_time=time.perf_counter() - self.start_time, 
                event_type="experiment/start",
                trigger=self.trigger_mapping["experiment/start"],
                log_file=log_file
                )
            
            self.loop_over_events(self.events, log_file)

            if self.send_trigger:
                self.raise_and_lower_trigger(self.trigger_mapping["experiment/end"])

            self.log_event(
                event_time=time.perf_counter() - self.start_time,
                event_type="experiment/end",
                trigger=self.trigger_mapping["experiment/end"],
                log_file=log_file
                )

        self.listener.stop_listener()  # Stop the keyboard listener


    def deliver_stimulus(self, event_type):
        if self.SGC_connectors:
            if "salient" in event_type:  # send to both fingers
                for connector in self.SGC_connectors.values():
                    connector.send_pulse()
            elif self.SGC_connectors and "target" in event_type: # send to the finger specified in the event type
                self.SGC_connectors[event_type.split("/")[-1]].send_pulse()

    def prepare_for_next_stimulus(self, event_type, next_event_type):
        if self.SGC_connectors:
            # after sending the trigger for the weak target stimulation change the intensity to the salient intensity
            if "target" in event_type: 
                self.SGC_connectors[event_type.split("/")[-1]].change_intensity(self.intensities["salient"])

            # check if next stimuli is weak, then lower based on which!
            if "target" in next_event_type:
                self.SGC_connectors[next_event_type.split("/")[-1]].change_intensity(self.intensities["weak"])

    def trial_block(self, ISI=1.5, n_sequences=None):
        n_sequences = n_sequences if n_sequences else self.n_sequences
        # Generate the sequence of events for the trial block
        trial_sequence_events = self.event_sequence(n_sequences=n_sequences, ISI=ISI, block_idx="trial", reset_QUEST=None)
        
        self.listener.start_listener()  # Start the keyboard listener
        self.loop_over_events(trial_sequence_events, log_file=None)
        self.listener.stop_listener()  # Stop the keyboard listener

    def raise_and_lower_trigger(self, trigger):
        setParallelData(trigger)

def generate_block_order(ISIs: List[float], n_repeats: int) -> List[int]:
    """
    Generate a sequence of block indices and 'break' markers.

    Parameters
    ----------
    ISIs : list of float
        The list of ISIs defining block types.
    n_repeats : int
        How many times to repeat the full transition set.

    Returns
    -------
    list
        A list containing block indices and "break" entries.
    """
    block_types = list(range(len(ISIs)))
    wanted_transitions = [(a, b) for a in block_types for b in block_types if a != b]

    order = []
    available_start_blocks = block_types.copy()

    for i in range(n_repeats):
        if not available_start_blocks:
            available_start_blocks = block_types.copy()
        start_block = np.random.choice(available_start_blocks)
        available_start_blocks.remove(start_block)

        tmp_order = build_block_order(wanted_transitions, start_blocks=[start_block])
        order.extend(tmp_order)
        if i != n_repeats - 1:
            order.append("break")

    return order




# UTILITIES
# -------------
def build_block_order(
    wanted_transitions: List[Tuple[int, int]],
    start_blocks: Optional[List[int]] = None
) -> List[int]:
    """
    Build a block order that exactly produces the given list of transitions.

    Parameters:
        wanted_transitions (list of tuples): Each tuple represents a transition (e.g., (0, 1)).
        start_blocks (list of int, optional): Block types to consider as starting points. 
                                              Defaults to all blocks present in wanted_transitions.

    Returns:
        list of int: A sequence of blocks that yields the specified transitions.

    Raises:
        ValueError: If no valid order can be found.
    """
    wanted_counter = Counter(wanted_transitions)

    # Infer block types from transition tuples
    block_types = list(set(b for pair in wanted_transitions for b in pair))

    def backtrack(path):
        if sum(wanted_counter.values()) == 0:
            return path

        last = path[-1]
        next_options = block_types[:]
        random.shuffle(next_options)

        for next_block in next_options:
            if next_block == last:
                continue
            candidate = (last, next_block)
            if wanted_counter[candidate] > 0:
                wanted_counter[candidate] -= 1
                result = backtrack(path + [next_block])
                if result:
                    return result
                wanted_counter[candidate] += 1  # backtrack

        return None

    # If not specified, start from any available block type
    if start_blocks is None:
        start_blocks = block_types
    else:
        start_blocks = [s for s in start_blocks if s in block_types]

    for start_block in random.sample(start_blocks, len(start_blocks)):
        result = backtrack([start_block])
        if result:
            return result

    raise ValueError("No valid order found")



def print_experiment_information(experiment):

    duration = experiment.estimate_duration()
    print(f"Estimated total duration: {duration/60:.1f} minutes ({duration:.0f} seconds)")
    experiment.setup_experiment()

    # Extract event_type from each dictionary
    event_types = [e.get("event_type") for e in experiment.events if isinstance(e, dict)]

    # Count each event_type
    event_counts = Counter(event_types)

    # Print the results
    for event_type, count in event_counts.items():
        print(f"{event_type}: {count}")

    # Count individual blocks
    block_counts = Counter(experiment.order)

    # Count transitions
    transitions = list(zip(experiment.order, experiment.order[1:]))
    transition_counts = Counter(transitions)
    # Display results
    print("Block counts:")
    for block, count in block_counts.items():
        print(f"  {block}: {count}")

    print("\nTransition counts:")
    for (a, b), count in transition_counts.items():
        print(f"  ({a} -> {b}): {count}")

def get_participant_info():
    pid = input("Enter participant ID: ").strip()

    while True:
        try:
            salient = float(input("Enter salient intensity (1.0–10.0): "))
            if salient not in VALID_INTENSITIES:
                raise ValueError
            break
        except ValueError:
            print("❌ Invalid input. Please enter a number between 1.0 and 10.0 in steps of 0.1.")

    weak = np.round(salient / 2, 1)
    if weak not in VALID_INTENSITIES:
        raise ValueError(f"Weak intensity {weak} is invalid. Adjust salient value.")

    print("\nParticipant Information:")
    print(f" ID: {pid}")
    print(f" Salient Intensity: {salient}")
    print(f" Weak Intensity: {weak}")


    confirm = input("Is this information correct? (y/n): ").strip().lower()
    if confirm != "y":
        print("Exiting experiment setup.")
        exit()

    return pid, {"salient": salient, "weak": weak}


if __name__ == "__main__":
    # --- Collect participant info ---
    participant_id, start_intensities = get_participant_info()

    # Setup logfile based on participant ID
    logfile = OUTPUT_PATH / f"{participant_id}_behavioural_data.csv"

    # check if it already exists
    if logfile.exists():
        i = 1
        while logfile.exists():
            logfile = OUTPUT_PATH / f"{participant_id}_behavioural_data_{i}.csv"
            i += 1

    print(f"Behavioural data will be saved to: {logfile}")


    # wait 2 seconds
    wait(2)

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
        send_trigger=False, # after running the trial block it is set to True
        logfile = logfile,
        SGC_connectors=connectors,
        prop_middle_index=[1/2, 1/2],
        break_sound_path=Path("utils/sound.wav")
    )

    print_experiment_information(experiment)
    #experiment.check_in_on_participant(message="Ready to begin practice block.")
    #experiment.trial_block(ISI=1.5, n_sequences=12) # practice block

    # possiblility to update intensities after practice
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


    experiment.send_trigger = True
    experiment.check_in_on_participant(message="Ready to begin main experiment.")
    experiment.run()



