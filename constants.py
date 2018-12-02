# This file is required for the PyGaze examples. It is automatically loaded by
# PyGaze, and will be used to provide default values for its classes.

import os


# DISPLAY
# The DISPTYPE determines what library is used to present visual stimuli. This
# can be "pygame" or "psychopy".
DISPTYPE = "psychopy"
# The DISPSIZE sets the resolution in pixels.
DISPSIZE = (1920, 1080)

# FILES AND FOLDERS
# Automatically detect what directory this file is in.
DIR = os.path.dirname(os.path.abspath(__file__))
# Construct a data directory to store data files in.
DATADIR = os.path.join(DIR, "data")
# Create the DATADIR if it does not exist yet.
if not os.path.isdir(DATADIR):
    os.mkdir(DATADIR)
# Ask the experimenter to write a file name for the event log file.
LOGFILENAME = raw_input("What is the file name? ")
# Construct the path to the log file.
LOGFILE = os.path.join(DATADIR, LOGFILENAME)
