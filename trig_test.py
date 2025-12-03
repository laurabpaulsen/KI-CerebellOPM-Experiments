import nidaqmx
import time

CHANNEL = "Dev1/port9/line0:7"

with nidaqmx.Task() as task:
    # On-demand digital output — NO timing configured
    task.do_channels.add_do_chan(CHANNEL)

    print(f"Using {CHANNEL}")

    for i in range(8):
        value = 1 << i                      # 1,2,4,8,...128
        bits = [(value >> b) & 1 for b in range(8)]

        print(f"Pulse on line {i} (value={value})")

        # ---- Pulse ----
        task.write(bits, auto_start=True)   # <-- crucial fix
        time.sleep(0.01)
        task.write([0]*8, auto_start=True)

    print("Done.")

