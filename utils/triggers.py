"""
Description: This file contains the code for sending triggers to the neuroimaging system.
"""
# -*- coding: utf-8 -*-
from psychopy import parallel


port = parallel.ParallelPort(address="Dev1/port9") # maybe port 9 at KI! or dev1
print(f"Parallel port {port} initialised.")

# Figure out whether to flip pins or fake it
try:
    port.setData(1)
except NotImplementedError:
    print(f"Parallel port {port} not implemented???.")
    def setParallelDataSQUID(code=1):
        if code > 0:
            # logging.exp('TRIG %d (Fake)' % code)
            print('TRIG %d (Fake)' % code)
            pass
else:
    port.setData(0)
    setParallelDataSQUID = port.setData

