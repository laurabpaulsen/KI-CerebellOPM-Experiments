import nidaqmx
from nidaqmx.constants import LineGrouping
import time

class ResponsePadListener:
    """
    Continuously polls 4 digital input lines on PCIe-6509.
    Each line represents one response button.
    """

    def __init__(self, device="Dev1", port="port6", num_lines=4):
        self.device = device
        self.port = port
        self.num_lines = num_lines
        self.task = nidaqmx.Task()

        # Create channel e.g. "Dev1/port7/line0:3"
        channel = f"{self.device}/{self.port}/line0:{self.num_lines-1}"

        self.task.di_channels.add_di_chan(
            channel,
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
        )

        print(f"Listening on {channel} ...")

    def listen(self, poll_interval=0.001):
        """
        Polls the hardware forever and prints whenever a button is pressed.
        """
        last_state = None

        try:
            while True:
                state = self.task.read()  # returns list of booleans
                if state != last_state:
                    last_state = state
                    # print states 0/1 for clarity
                    print("Button states:", state)

                time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("Stopped.")

        finally:
            self.task.close()


if __name__ == "__main__":
    listener = ResponsePadListener(device="Dev1", port="port6", num_lines=4)
    listener.listen()
