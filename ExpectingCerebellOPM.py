"""

"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))


import time
from typing import Union
import numpy as np
import copy

from utils.triggers_nidaqmx import setParallelData
from utils.responses_nidaqmx import NIResponsePad
#from utils.responses import KeyboardListener

from psychopy.clock import CountdownTimer
from psychopy.core import wait

from collections import Counter
from utils.params import connectors

VALID_INTENSITIES = np.arange(1.0, 10.1, 0.1).round(1).tolist()
STIM_DURATION = 100  # 0.1 ms

BUTTONS_INDEX = ["1", "b"]  # blue
BUTTONS_MIDDLE = ["2", "y"]  # yellow


OUTPATH = Path(__file__).parent / "output" / "ExpectingCerebellOPM"

if not OUTPATH.exists():
    OUTPATH.mkdir(parents=True, exist_ok=True)

class ExpectationExperiment:
    LOGHEADER = "block,stim_site_first,time_first,stim_site_second,time_second,repeated,expected,response,RT,correct\n"
    def __init__(
        self, ISI: float, 
        trigger_mapping:dict, 
        outpath: Union[str, Path], 
        connectors: dict,
        prop_expected_unexpected:list = [0.75, 0.25], 
        first_stimuli = ["middle", "index"], 
        second_stimuli = ["middle", "index"], 
        behavioural_task:Union[bool, str] = "second",
        max_response_time: float = 4,
        n_events_per_block = 100,
        rng_interval =  (1, 1.5),
        n_repeats_per_block = 2,
        send_trigger: bool = True,
        break_sound_path: Union[str, Path] = None,
        random_responses: bool = False,
        response_keys: dict = {
            "index": BUTTONS_INDEX,
            "middle": BUTTONS_MIDDLE
        }
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
        behavioural_task : False | "first" |  "second" | "catch"
        wait_after_response : float 
            determines the wait time before the next trial after a keypress. Only used if behavioural task is not False.
        
        """
        self.ISI: float = ISI
        self.trigger_mapping: dict = trigger_mapping
        self.prop_exp_unexp = prop_expected_unexpected
        self.SGC_connectors = connectors
        self.first_stimuli = first_stimuli
        self.second_stimuli = second_stimuli
        self.outpath: Path = Path(outpath)
        self.stimuli_pairs = self.define_stimuli_pairs()
        self.n_events_per_block = n_events_per_block
        self.n_repeats_per_block = n_repeats_per_block
        self.break_sound_path = break_sound_path
        self.countdown_timer = CountdownTimer()
        self.rng_IPI = np.random.Generator(np.random.PCG64())
        self.rng_interval = rng_interval
        self.max_response_time = max_response_time  # in seconds
        self.behavioural_task = behavioural_task
        self.send_trigger = send_trigger
        self.random_responses = random_responses

        # Map physical lines to response labels used by the experiment.
        # Adjust mapping dict so line indices match the pad wiring.
        line_to_label = {
            0: "b", # blue
            1: "y", # yellow
            2: "g", # green
            3: "r", # red
        }

        self.listener = NIResponsePad(
            device="Dev1",
            port="port6",
            num_lines=4,
            mapping=line_to_label,
            poll_interval_s=0.0005,
            debounce_ms=30,
            timestamp_responses=False,
        )

        # Keep the existing logic: which labels count as correct for each second stimulus
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

                    for _ in range(n_trials):
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
                                "behaviour": self.behavioural_task,
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

        print(f"Total number of events: {len(self.blocks)}")
    
    #def play_break_sound(self):
    #    # Play a sound to indicate a break
    #    if self.break_sound_path:
    #        PlaySound(str(self.break_sound_path), SND_FILENAME)

    def raise_and_lower_trigger(self, trigger):
        setParallelData(trigger)
        

    def calculate_duration(self):
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
            # break time
            total_time += 60  # assuming fixed 60 seconds break between blocks

            for event in block:
                total_time += self.ISI  # ISI time
                total_time += event["IPI"]  # Inter-pair interval
                if event["behaviour"]:
                    total_time += self.max_response_time
                
                # trigger durations
                total_time += 3 * 0.005  # for first and second stimuli and response
            
        return total_time

    def deliver_stimulus(self, site: str):
        if self.SGC_connectors:
            self.SGC_connectors[site].send_pulse()

    def initialise_block(self):
        self.check_in_on_participant("Starting new block. Check in on the participant.")
    
    def run(self):
        # Start the listener once at the start
        self.listener.start_listener()
        self.start_time = time.perf_counter()

        with open(self.outpath, "w") as log_file:
            log_file.write(self.LOGHEADER)

            for i_block, block in enumerate(self.blocks):
                self.initialise_block()
                for i, event in enumerate(block):
                    print(f" Trial {i + 1} of {len(block)} in block {i_block + 1} of {len(self.blocks)}")
                    response, correct, response_time = None, None, None

                    time_first = time.perf_counter()
                    self.deliver_stimulus(event["first"])
                    self.raise_and_lower_trigger(event["trigger_first"])
                    wait(self.ISI)
                    time_second = time.perf_counter()
                    self.deliver_stimulus(event["second"])
                    self.raise_and_lower_trigger(event["trigger_second"])

                    # Only poll responses during the response window
                    self.countdown_timer.reset(self.max_response_time)

                    if self.random_responses:  # for testing only
                        response = np.random.choice(["1", "2"])
                        correct = response in self.response_keys[event["second"]]
                        self.raise_and_lower_trigger(self.trigger_mapping["response"])
                    else:
                        self.listener.reset_response()  # <- clear any lingering press from previous trial
                        while self.countdown_timer.getTime() > 0:
                            candidate = self.listener.get_response()
                            if candidate:
                                response = candidate
                                response_time = time.perf_counter() - time_second
                                correct = response in self.response_keys[event["second"]]
                                self.raise_and_lower_trigger(self.trigger_mapping["response"])
                                print(f" Response: {response} | Correct: {correct} | RT: {response_time:.3f} s")
                                break

                    # Log the event
                    self.log_event(
                        i_block, event["first"], time_first, event["second"],
                        time_second, event["repeated"], event["expected"],
                        response, response_time, correct, log_file
                    )

                    # Wait for the inter-pair interval
                    wait(event["IPI"])

        self.listener.stop_listener()
        print("Experiment finished.")

    def log_event(self, block="NA", stim_site_first="NA", time_first="NA", stim_site_second="NA", time_second="NA", repeated="NA", expected="NA", response="NA", RT="NA", correct="NA", log_file=None):
        if log_file:
            log_file.write(f"{block},{stim_site_first},{time_first},{stim_site_second},{time_second},{repeated},{expected},{response},{RT},{correct}\n")

    def check_in_on_participant(self, message: str = "Check in on the participant.", log_file=None):
        if self.send_trigger:
            self.raise_and_lower_trigger(self.trigger_mapping["break/start"])

        self.log_event(block="break_start", time_first=time.perf_counter() - self.start_time, log_file=log_file)

        #self.play_break_sound()
        input(message + " Press Enter to continue...")
        
        if self.send_trigger:
            self.raise_and_lower_trigger(self.trigger_mapping["break/end"])
            self.log_event(block="break_end", time_first=time.perf_counter() - self.start_time, log_file=log_file)
        
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



def create_trigger_mapping():
    response_bit = 1
    second_bit = 2
    expected_bit = 4
    repetition = 8

    index_bit = 16
    middle_bit = 32

    break_bit_start = 64
    break_bit_end = 128

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

        "break/start": break_bit_start,
        "break/end": break_bit_end
    }

    return trigger_mapping

if __name__ in "__main__":

    
    participant_id, intensity = get_participant_info()

    break_sound_path = Path(__file__).parents[1] / "utils" / "sound.wav"

    # wait 2 seconds
    wait(2)

    for finger, connector in connectors.items():
        connector.set_pulse_duration(STIM_DURATION)
        connector.change_intensity(intensity)

    trigger_mapping = create_trigger_mapping()

    experiment = ExpectationExperiment(
        ISI=0.54,
        trigger_mapping=trigger_mapping,
        behavioural_task="second",
        connectors=connectors,
        n_events_per_block = 100,
        rng_interval =  (1, 1.5),
        n_repeats_per_block = 2,
        max_response_time=2, # seconds
        #random_responses=True,  # REMEMBER TO REMOVE THIS IN REAL EXPERIMENTS
        outpath=OUTPATH / f"{participant_id}_{intensity}.csv",
        break_sound_path=break_sound_path
    )

    duration = experiment.calculate_duration()
    print(f"Estimated duration: {duration/60} minutes")
    
    experiment.run()