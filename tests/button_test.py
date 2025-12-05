import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))

from utils.responses_nidaqmx import NIResponsePad

if __name__ == "__main__":
    listener = NIResponsePad(device="Dev1", port="port6", num_lines=4)
    listener.start_listener()
    try:
        while True:
            response = listener.get_response()
            if response is not None:
                print(f"Button pressed: {response}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        listener.stop_listener()