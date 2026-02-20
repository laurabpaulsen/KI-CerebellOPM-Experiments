"""
This script is used to reset the lines of the specified ports to 0. This can be useful if the lines were left in a high state after an experiment, which can cause issues with subsequent experiments that expect the lines to be in a low state at the start.
"""

# -*- coding: utf-8 -*-


import nidaqmx
from nidaqmx.constants import LineGrouping

PORTS = ["Dev1/port9/line0:7", "Dev1/port0/line0:7", "Dev1/port3/line0:7"]  # All 8 lines of port 0, 3, 9

def init_tasks():
    
    tasks = []
    
    for port in PORTS:
        task = nidaqmx.Task(new_task_name=f"Reset Port Task {port.split('/')[1]}")  # Name task based on port

        task.do_channels.add_do_chan(
            port,
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
        )
        tasks.append(task)

    return tasks

        
def lower_lines(tasks):
    for task in tasks:
        task.write(0, auto_start=True)  # Set lines to desired code without starting yet 
   

def close_tasks(tasks):

    for task in tasks:
        task.close()

if __name__ == "__main__":
    tasks = init_tasks()
    lower_lines(tasks)
    close_tasks(tasks)
  