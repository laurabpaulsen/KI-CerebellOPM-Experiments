import nidaqmx
import time

# Use all 8 lines on port 5
CHANNEL = "Dev1/port5/line0:7"

def pulse(value, duration=0.01):
    """
    value: 8-bit integer (0–255)
    duration: seconds to hold the value
    """
    bits = [(value >> i) & 1 for i in range(8)]

    task.write(bits)
    time.sleep(duration)
    task.write([0]*8)  # reset to zero


with nidaqmx.Task() as task:
    task.do_channels.add_do_chan(CHANNEL)
    print(f"Using {CHANNEL}")

    # Test sequence: 1, 2, 4, 8... (powers of two)
    for i in range(8):
        val = 1 << i
        print(f"Sending {val} on line {i}")
        pulse(val, duration=0.01)

    print("Done.")
