import os
from .SGC_connector import SGCConnector, SGCFakeConnector
from pathlib import Path
# check whether it is running on mac or windows

if os.name == "posix":
    # macOS
    index_connector_port = "/dev/tty.usbserial-A50027EN"
    middle_connector_port = "/dev/tty.usbserial-A50027ER"
else:
    # Windows
    index_connector_port = "COM6"
    middle_connector_port = "COM7"


connectors = {
        #"middle":  SGCConnector(port=middle_connector_port, intensity_codes_path=Path("intensity_code.csv"), start_intensity=1),
        "index": SGCConnector(port=index_connector_port, intensity_codes_path=Path("intensity_code.csv"), start_intensity=1),
        "middle": SGCFakeConnector(intensity_codes_path=Path("intensity_code.csv"), start_intensity=1),
        #"index": SGCFakeConnector(intensity_codes_path=Path("intensity_code.csv"), start_intensity=1)
    }