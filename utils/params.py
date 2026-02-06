import numpy as np
import os
from .SGC_connector import SGCConnector, SGCFakeConnector
from pathlib import Path

# Params for both experiments
VALID_INTENSITIES = np.arange(1.0, 10.1, 0.1).round(1).tolist()
STIM_DURATION = 100  # 0.1 ms

TARGET_1 = "index"
TARGET_2 = "middle"
TARGET_1_KEYS = ["1", "b"]
TARGET_2_KEYS = ["2", "y"]

# Params for BreathingCerebellOPM
DIFF_SALIENT_WEAK = 0.3  # difference between salient and weak intensity
N_REPEATS_BLOCKS = 5
N_SEQUENCE_BLOCKS = 6
RESET_QUEST = 2 # how many blocks before resetting QUEST
ISIS = [1.29, 1.44, 1.57, 1.71] 

# Params for ExpectingCerebellOPM
ISI=0.701  # seconds
RNG_INTERVAL=(1., 1.25)  # seconds
N_EVENTS_PER_BLOCK=160  # number of stimulus pairs per block



path = Path(__file__).parents[1] 

# check whether it is running on mac or windows

if os.name == "posix":
    # macOS
    middle_connector_port = "/dev/tty.usbserial-A50027EN"
    index_connector_port = "/dev/tty.usbserial-A50027ER"

    connectors = {
        "middle": SGCConnector(port=middle_connector_port, intensity_codes_path=path / "intensity_code.csv", start_intensity=1),
        "index": SGCConnector(port=index_connector_port, intensity_codes_path=path / "intensity_code.csv", start_intensity=1),  
        #"middle": SGCFakeConnector(intensity_codes_path=path / "intensity_code.csv", start_intensity=1),
        #"index": SGCFakeConnector(intensity_codes_path=path / "intensity_code.csv", start_intensity=1)
        }
else:
    # Windows
    index_connector_port = "COM5"
    middle_connector_port = "COM4"
    connectors = {
            "middle":  SGCConnector(port=middle_connector_port, intensity_codes_path=path / "intensity_code.csv", start_intensity=1),
            "index": SGCConnector(port=index_connector_port, intensity_codes_path=path / "intensity_code.csv", start_intensity=1)
        }


