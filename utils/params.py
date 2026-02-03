import os
from .SGC_connector import SGCConnector, SGCFakeConnector
from pathlib import Path

from psychopy import visual, monitors

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


monitor = monitors.Monitor('testMonitor')  # you can change 'testMonitor' to your monitor name
monitor.setDistance(60)  # set the viewing distance in cm
monitor.setSizePix((1920, 1080))  # set the resolution of your monitor
monitor.setWidth(34.5)  # set the physical width of your monitor in cm


win = visual.Window(
    color="grey",
    fullscr=True, 
    monitor=monitor,
    screen=1,
    checkTiming=False
    )