import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))

from utils.triggers_nidaqmx import setParallelData, 



# keys to test
keys_to_test = [
    "stim/salient",
    "target/middle",
    "target/index",
    "response/index/correct",
    "response/middle/correct",
    "break/start",
    "break/end",
    "experiment/start",
    "experiment/end",
]

def create_trigger_mapping( stim = 1, target = 2, middle = 4, index = 8,response = 16, correct = 32, incorrect = 64):
    trigger_mapping = {
        "stim/salient": stim,
        "target/middle": target + middle,
        "target/index": target + index,
        "response/index/correct": response + index + correct,
        "response/middle/incorrect": response + middle + incorrect,
        "response/middle/correct": response + middle + correct,
        "response/index/incorrect": response + index + incorrect,
        "break/start": 128,
        "break/end": 129,            
        "experiment/start": 254,
        "experiment/end": 255
        }

    return trigger_mapping
        

mapping = create_trigger_mapping()

print("Starting trigger test...\n")
for key in keys_to_test:
    bits = mapping[key]
    print(f"Sending trigger: {key} -> {bits}")
    setParallelData(bits)
    time.sleep(0.5)

print("\nTrigger test completed.")