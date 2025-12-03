import time
from utils.triggers_nidaqmx import setParallelData, create_trigger_mapping

print("Loading trigger mapping...")
mapping = create_trigger_mapping()

print("Starting trigger test...\n")

# List of keys you want to test
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

for key in keys_to_test:
    bits = mapping[key]
    print(f"Sending trigger: {key} -> {bits}")
    setParallelData(bits)
    time.sleep(0.5)

print("\nDone. If everything is wired correctly, you should see all of these pulses.")
