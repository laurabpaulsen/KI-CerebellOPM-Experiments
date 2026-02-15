"""

"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import time
from typing import Union
import numpy as np
import copy

from utils.responses_nidaqmx import NIResponsePad
from utils.triggers_nidaqmx import setParallelData

from psychopy.clock import CountdownTimer
from psychopy.core import wait


from utils.params import (
    VALID_INTENSITIES, STIM_DURATION, 
    TARGET_1, TARGET_1_KEYS,
    TARGET_2, TARGET_2_KEYS,
    N_EVENTS_PER_BLOCK, RNG_INTERVAL, ISI,
    connectors
)

from utils.fixation_display import FixationDisplay


OUTPATH = Path(__file__).parent / "output" / "ExpectingCerebellOPM"

if not OUTPATH.exists():
    OUTPATH.mkdir(parents=True, exist_ok=True)

class ExpectationExperiment:
    LOGHEADER = "block,stim_site_first,time_first,stim_site_second,time_second,repeated,expected,response,RT,correct,intensity\n"
    def __init__(
        self, ISI: float, 
        trigger_mapping:dict,
        connectors: dict, 
        outpath: Union[str, Path, None] = None, 
        prop_expected_unexpected:list = [0.75, 0.25], 
        first_stimuli = ["middle", "index"], 
        second_stimuli = ["middle", "index"], 
        n_events_per_block = 100,
        rng_interval =  (1, 1.5),
        n_repeats_per_block = 2,
        send_trigger: bool = True,
        response_keys: dict = {
            TARGET_1: TARGET_1_KEYS,
            TARGET_2: TARGET_2_KEYS,
        },
        practise_mode: bool = False,
        intensity: float = 2.5,
        ):
        """
        
        Parameters
        ----------
        ISI : int
            the interval between the first and second stimulation in seconds
        prop_expected_unexpected : list[float]
            the proportion of expected and unexpected stimuli. Sums to 1. 
        outpath : str or Path
        first_stimuli : list[str]
        second_stimuli : list[str]

        
        """
        self.ISI: float = ISI
        self.trigger_mapping: dict = trigger_mapping
        self.prop_exp_unexp = prop_expected_unexpected
        self.SGC_connectors = connectors
        self.first_stimuli = first_stimuli
        self.second_stimuli = second_stimuli
        self.outpath = Path(outpath) if outpath else Path("output.csv")
        self.stimuli_pairs = self.define_stimuli_pairs()
        self.n_events_per_block = n_events_per_block
        self.n_repeats_per_block = n_repeats_per_block
        self.countdown_timer = CountdownTimer()
        self.rng_IPI = np.random.Generator(np.random.PCG64())
        self.rng_interval = rng_interval
        self.send_trigger = send_trigger
        self.practise_mode = practise_mode
        self.intensity = intensity

        self.display = FixationDisplay(screen_index=0)
        self.break_message = 'Time for a break!'
        self.env_change_message = 'The statistical regularites between the first and the second stimulus may have changed now! Take a little break.'
        # Map lines to response labels used by the experiment.
        line_to_label = {
            0: "b", # blue
            1: "y", # yellow
        }
        
        self.listener = NIResponsePad(
            device="Dev1",
            port="port6",
            num_lines=2,
            mapping=line_to_label,
            poll_interval_s=0.0005,
            debounce_ms=30,
            timestamp_responses=False,
        )
        self.response_keys = response_keys
        self.prep_events()


    def define_stimuli_pairs(self):
        stim_pairs = {first: [] for first in self.first_stimuli}
        
        for first in self.first_stimuli:
            for second_exp in self.second_stimuli:
                for second_unexp in self.second_stimuli:
                    if not second_exp == second_unexp:
                        pair = {"expected": second_exp, "unexpected": second_unexp}

                        stim_pairs[first].append(pair)

        return stim_pairs    

    def prep_events(self):

        n_blocks = len(self.stimuli_pairs[self.first_stimuli[0]])

        # deep copy so we don't mutate the original lists across blocks
        tmp_stim_pairs = copy.deepcopy(self.stimuli_pairs)

        all_blocks = []

        for _ in range(n_blocks):
            block_events = []

            # choose one stimuli pair per "first" stimulus
            for first in self.first_stimuli:
                pair = np.random.choice(tmp_stim_pairs[first])
                tmp_stim_pairs[first].remove(pair)

                # generate expected & unexpected trials
                for exp, prob in zip(["expected", "unexpected"], self.prop_exp_unexp):
                    n_trials = int(self.n_events_per_block/2 * prob)

                    for _ in range(n_trials+1):
                        second = pair[exp]
                        repeated_label = "repeated" if first == second else "unrepeated"
                        trigger_second_key = f"second/{second}/{exp}/{repeated_label}"

                        block_events.append(
                            {
                                "first": first,
                                "trigger_first": self.trigger_mapping[f"first/{first}"],
                                "second": second,
                                "trigger_second": self.trigger_mapping[trigger_second_key],
                                "expected": exp,
                                "repeated": repeated_label,
                                "IPI": self.rng_IPI.uniform(*self.rng_interval),
                            }
                        )

            # internal repeats/shuffling
            for _ in range(self.n_repeats_per_block):
                shuffled = block_events.copy()
                np.random.shuffle(shuffled)
                all_blocks.append(shuffled)

        # intermix the blocks globally
        np.random.shuffle(all_blocks)

        self.blocks = all_blocks

    
    def show_fixation(self, color="white"):
        self.display.show_fixation(color=color)



    def raise_and_lower_trigger(self, trigger):
        setParallelData(trigger)

        
    def calculate_duration(self, response_time: float = 1.0) -> float:
        """
        Calculates the total duration of the experiment in seconds.

        Returns
        -------
        float
            Total duration of the experiment.
        """
        total_time = 0
        
        for block in self.blocks:
            total_time += 2 # sleep after initialising new block

            for event in block:
                total_time += self.ISI  # ISI time
                total_time += event["IPI"]  # Inter-pair interval
                total_time += response_time
                
            
        return total_time

    def deliver_stimulus(self, site: str):
        if self.SGC_connectors:
            self.SGC_connectors[site].send_pulse()

    def run(self):
        # Start the listener once at the start
        self.listener.start_listener()
        self.start_time = time.perf_counter()

        with open(self.outpath, "w") as log_file:
            log_file.write(self.LOGHEADER)

            for i_block, block in enumerate(self.blocks):
                for i, event in enumerate(block):
                    self.show_fixation()
                    print(f" Trial {i + 1} of {len(block)} in block {i_block + 1} of {len(self.blocks)}. Stimuli: {event['first']} - {event['second']}")

                    # break in the middle of the block
                    if i == len(block)//2 and not self.practise_mode:
                        # break message
                        self.display.show_text(self.break_message)
                        self.check_in_on_participant("Halfway through the block. Check in on the participant.", ask_for_update=False)
                        self.show_fixation()


                    time_first = time.perf_counter()
                    self.deliver_stimulus(event["first"])
                    self.raise_and_lower_trigger(event["trigger_first"])
                    wait(self.ISI)
                    time_second = time.perf_counter()
                    self.deliver_stimulus(event["second"])
                    self.raise_and_lower_trigger(event["trigger_second"])

                    self.listener.reset_response()  # <- clear any lingering press from previous trial
                    while True:
                        candidate = self.listener.get_response()
                        if candidate:
                            response = candidate
                            response_time = time.perf_counter() - time_second
                            correct = response in self.response_keys[event["second"]]
                            self.raise_and_lower_trigger(self.trigger_mapping["response"])
                            print(f"{event['second']} {event['repeated']}, {event['expected']} - Response: {response} | Correct: {correct} | RT: {response_time:.3f} s")
                            break

                    # Log the event
                    self.log_event(
                        i_block, event["first"], time_first, event["second"],
                        time_second, event["repeated"], event["expected"],
                        response, response_time, correct, self.intensity, log_file
                    )


                    ## Wait for the inter-pair interval
                    wait(event["IPI"])

                # present env change message between blocks
                if not self.practise_mode and i_block < len(self.blocks) - 1:
                    self.display.show_text(self.env_change_message)
                    self.check_in_on_participant("Starting new block. Check in on the participant.", ask_for_update=True)


        self.listener.stop_listener()
        print("Experiment finished.")

    def log_event(self, block="NA", stim_site_first="NA", time_first="NA", stim_site_second="NA", time_second="NA", repeated="NA", expected="NA", response="NA", RT="NA", correct="NA", intensity = "NA", log_file=None):
        if log_file:
            log_file.write(f"{block},{stim_site_first},{time_first},{stim_site_second},{time_second},{repeated},{expected},{response},{RT},{correct},{intensity}\n")

    def check_in_on_participant(self, message: str = "Check in on the participant.", log_file=None, ask_for_update: bool = True):
        if self.send_trigger:
            self.raise_and_lower_trigger(self.trigger_mapping["break/start"])
            self.log_event(block="break_start", time_first=time.perf_counter() - self.start_time, log_file=log_file)

        input(message + " Press Enter to continue...")

        if ask_for_update:
            self.ask_for_update_intensity()
        
        if self.send_trigger:
            self.raise_and_lower_trigger(self.trigger_mapping["break/end"])
            self.log_event(block="break_end", time_first=time.perf_counter() - self.start_time, log_file=log_file)
        
        wait(2)

    def ask_for_update_intensity(self):
        # possiblility to update intensities after practice
        while True:
            update = input("\nUpdate salient intensity? (y/n): ").strip().lower()
            # check if y or n, otherwise ask again
            if update not in ["y", "n"]:
                print("❌ Invalid input. Please enter 'y' or 'n'.")
                continue
            break
        if update == "y":
            while True:
                try:
                    new = float(input(f"Old intensity = {self.intensity}. Enter new salient intensity (1.0–10.0): "))
                    if new not in VALID_INTENSITIES:
                        raise ValueError
                    break
                except ValueError:
                    print("❌ Invalid input. Enter a number between 1.0 and 10.0 in steps of 0.1.")

            # apply to experiment
            self.intensity = new

            # push new values to the devices
            for side, connector in self.SGC_connectors.items():
                connector.change_intensity(new)

            # wait
            wait(2)

def get_participant_info():
    pid = input("Enter participant ID: ").strip()

    while True:
        try:
            salient = float(input("Enter intensity (1.0–10.0): "))
            if salient not in VALID_INTENSITIES:
                raise ValueError
            break
        except ValueError:
            print("❌ Invalid input. Please enter a number between 1.0 and 10.0 in steps of 0.1.")


    print("\nParticipant Information:")
    print(f" ID: {pid}")
    print(f" Intensity: {salient}")

    confirm = input("Is this information correct? (y/n): ").strip().lower()
    if confirm != "y":
        print("Exiting experiment setup.")
        exit()

    return pid, salient



def create_trigger_mapping(response_bit = 1, second_bit = 2, expected_bit = 4, repetition = 8, index_bit = 16, middle_bit = 32, break_bit_start = 64, break_bit_end = 128):
    trigger_mapping = {
        # FIRST STIMULI
        "first/index": index_bit,
        "first/middle": middle_bit,

        # SECOND STIMULI
        # index finger
        "second/index/expected/repeated": second_bit + index_bit + expected_bit + repetition,
        "second/index/expected/unrepeated": second_bit + index_bit + expected_bit,
        "second/index/unexpected/repeated": second_bit + index_bit  + repetition,
        "second/index/unexpected/unrepeated": second_bit + index_bit,

        # middle finger
        "second/middle/expected/repeated": second_bit + middle_bit + expected_bit + repetition,
        "second/middle/expected/unrepeated": second_bit + middle_bit + expected_bit,
        "second/middle/unexpected/repeated": second_bit + middle_bit  + repetition,
        "second/middle/unexpected/unrepeated": second_bit + middle_bit,

        # RESPONSE
        "response": response_bit,

        # BREAKS
        "break/start": break_bit_start,
        "break/end": break_bit_end,
        
        # EXPERIMENT START/END
        "experiment/start": 254,
        "experiment/end": 255
    }

    return trigger_mapping

if __name__ in "__main__":    
    participant_id, intensity = get_participant_info()

    for finger, connector in connectors.items():
        connector.set_pulse_duration(STIM_DURATION)
        connector.change_intensity(intensity)

    trigger_mapping = create_trigger_mapping()
    outpath = OUTPATH / f"{participant_id}_{intensity}.csv"

    # check whether the output file already exists
    if outpath.exists():
        # append a number to the filename
        i = 1
        while True:
            new_outpath = OUTPATH / f"{participant_id}_{intensity}_{i}.csv"
            if not new_outpath.exists():
                outpath = new_outpath
                break
            i += 1

    experiment = ExpectationExperiment(
        ISI=ISI,
        trigger_mapping=trigger_mapping,
        connectors=connectors,
        n_events_per_block = N_EVENTS_PER_BLOCK,
        rng_interval = RNG_INTERVAL,
        n_repeats_per_block = 2,
        outpath=outpath,
        intensity=intensity
    )

    average_rt = 0.9  # average response time in seconds
    duration = experiment.calculate_duration(response_time=average_rt)
    print(f"Estimated active duration: {duration/60} minutes with a response time of {average_rt} seconds.")
    experiment.show_fixation()
    input("Press Enter to begin the experiment...")


    if experiment.send_trigger:
        experiment.raise_and_lower_trigger(trigger_mapping["experiment/start"])

    experiment.run()


    if experiment.send_trigger:
        experiment.raise_and_lower_trigger(trigger_mapping["experiment/end"])

    