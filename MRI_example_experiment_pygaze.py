# MRC CBU MRI SYNC EXAMPLE
# This example illustrates how to use the `scansync` library. This library was
# written to synchronise experiments with the MEG and MRI scanners at the
# MRC Cognition and Brain Sciences Unit.

from pygaze.display import Display
from pygaze.screen import Screen
from pygaze.keyboard import Keyboard
from pygaze.logfile import Logfile
import pygaze.libtime as timer

from scansyn.mri import MRITriggerBox


# # # # #
# INITIALISE

# Create a Display object to present stuff on the projector. The Display gets
# its initialisation parameters from the constants.py script; automatically!
disp = Display()

# Create a Screen object that we can use to present miscellaneous messages.
screen = Screen()
# Draw a "Loading..." message on the screen.
screen.draw_text("Loading, please wait...", fontsize=32)
# Display the message using the Display object. This requires the display to
# be filled with the screen (happens in the background), and then to be shown.
# The show function returns a timestamp.
disp.fill(screen)
exp_start_time = disp.show()

# Create a Keyboard object to allow the experimenter to pace the experiment.
keyboard = Keyboard(keylist=None, timeout=None)

# Create a new Logfile object to log events to.
log = Logfile()
# Write a header to the log file.
log.write(["time", "event"])

# Create a MRITriggerBox instance. This will allow you to wait for the
# scanner's pulses, and also to detect button presses from the participant.
mri = MRITriggerBox()


# # # # #
# PREPARE SCREENS

# Create a string with instructions for the experiment.
instructions = \
"""
When the fixation cross is visible, you can press the left or the right key.

You can press the keys whenever you feel like it.

Try to make your key presses unpredictable.

(The experimenter will start the experiment when the scanner is ready.)
"""

# Create a Screen to present the instructions on.
instruction_screen = Screen()
instruction_screen.draw_text(instructions, fontsize=32)

# Create a 'Ready?' screen for the participant.
ready_screen = Screen()
ready_screen.draw_text("Press any button to start!", fontsize=32)

# The fixation screen will have a '+' in the centre of the screen.
fix_screen = Screen()
fix_screen.draw_fixation(fixtype='cross', lw=5, diameter=50)


# # # # #
# EXPERIMENT

# Show the instructions.
disp.fill(instruction_screen)
t1 = disp.show()
log.write([t1, "instructions_onset"])

# Wait until the experimenter presses a key.
key, presstime = keyboard.get_key()
log.write([presstime, "instructions_offset"])

# Wait for a scanner pulse to come in.
mri.wait_for_sync(timeout=None)
log.write([timer.get_time(), "mri_sync_pulse"])

# Show the participant the "Ready?" screen.
disp.fill(ready_screen)
ready_time = disp.show()
log.write([ready_time, "ready_screen"])

# Wait for the participant to press any button to start the experiment.
button, presstime = mri.wait_for_button_press(timeout=None)
log.write([timer.get_time(), "ready_press"])

# Show the fixation screen.
disp.fill(fix_screen)
t0 = disp.show()
log.write([t0, "fixation_onset"])

# Run for 10 minutes (10 minutes * 60 seconds * 1000 milliseconds).
exptime = 10 * 60 * 1000
while timer.get_time() - t0 < exptime:

    # Wait for a new button press from the participant. The only allowed
    # buttons are B1 (leftmost) and B4 (rightmost).
    button, presstime = mri.wait_for_button_press(allowed=["B1", "B4"], \
        timeout=None)

    # Log the button press.
    log.write([timer.get_time(), "buttonpress_%s" % (button)])


# # # # #
# CLOSE

# Tell the participant that the experiment is done.
end_text = \
"""This is the end of the experiment. Well done!

Please lay still for a bit; we will be with you shortly.
"""
screen.clear()
screen.draw_text(end_text, fontsize=32)
disp.fill(end_text)
exp_end_time = disp.show()
log.write([exp_end_time, "fixation_offset"])

# Close the log file.
log.close()

# Close the MRITriggerBox.
mri.close()

# Wait until the experimenter presses a button on the keyboard.
key, presstime = keyboard.get_key()

# Close the display.
disp.close()
