import os
# check whether it is running on mac or windows

if os.name == "posix":
    # macOS
    index_connector_port = "/dev/tty.usbserial-A50027EN"
    middle_connector_port = "/dev/tty.usbserial-A50027ER"
else:
    # Windows
    index_connector_port = "COM6"
    middle_connector_port = "COM7"