#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# MRC CBU PYTHON SCANNING SYNC
#
# This library is intended to allow for easy communication between Python
# experiments and the MEG and MRI scanners at the MRC Cognition and Brain
# Sciences Unit (CBU). The implementation is intended for the CBU setup only,
# and interfaces with the National Instruments setups in the MEG and MRI labs.
#
# Author: Edwin Dalmaijer
# Email: Edwin.Dalmaijer@mrc-cbu.cam.ac.uk

import copy
import time

import nidaqmx
from nidaqmx.constants import LineGrouping


class MEGTriggerBox:
    
    def __init__(self, device="Dev1"):
        
        """Initialises the MEG Trigger Box. Note that the button box buttons'
        names and channels are hard-coded into the initialisation function.
        The same is true for the trigger channels.

        Keyword Arguments
        
        device              -   String indicating the name of the device.
                                Don't mess with this unless you know what
                                you're doing. Default = "Dev1"
        """
        
        # Create a list with all short-hand button names and associated ports.
        self._button_list = ["Rr", "Ly", "Rb", "Ry", "Rg"]
        # Select all associated button channels.
        self._button_channels = "port0/line0:4"
        
        # Select all trigger channels.
        self._trigger_channels = "port2/line0:7"
        
        # INITIALISE
        print("\nInitialising connection to the NI box...")
        # Initialise the system.
        system = nidaqmx.system.System.local()
        # Present the available devices.
        print("\tAvailable NI devices:")
        for dev_name in system.devices:
            print("\t\t%s" % (dev_name))
        # Connect to the passed device.
        self._dev_name = device
        self._dev = system.devices[self._dev_name]
        
        print("\nConnection established with '%s'!" % (self._dev_name))
        print("\tDevice: %s" % (self._dev))
        print("\nChannel details:")
        print("Buttons: %s" % (self._button_channels))
        print("Triggers: %s" % (self._trigger_channels))
    
    
    def get_button_state(self, button_list=None):
        
        """Returns a single sample from the button channels.
        
        Keyword Arguments
        
        button_list         -   List of button names, or None to automatically
                                poll all the buttons. Default = None
        
        Returns
        
        button_list, state  -   button_list is a list of all button names, and
                                state is a list of the associated Booleans.
        """
        
        # Create a new Task to listen in on the button channels.
        with nidaqmx.Task() as task:
            # Add the digital input (di) channels.
            task.di_channels.add_di_chan( \
                "%s/%s" % (self._dev_name, self._button_channels), \
                line_grouping=LineGrouping.CHAN_PER_LINE)
            # Get a single sample from the digital input channels.
            state = task.read(number_of_samples_per_channel=1, \
                timeout=0.001)
        
        # Unwrap state, which is a list of lists of samples.
        # Example: [[False], [False], [False], [False], [False]]
        # We want instead: [False, False, False, False, False]
        for i, b in enumerate(state):
            state[i] = b[0]

        # Select all buttons if no specific ones are requested.
        if button_list is None:
            return copy.deepcopy(self._button_list), state

        # Return only the requested buttons.
        else:
            l = []
            for b in button_list:
                if b not in self._button_list:
                    raise Exception("ERROR: Unknown button '%s'; available buttons: %s" \
                        % (b, self._button_list))
                i = self._button_list.index(b)
                l.append(state[i])
            return button_list, l
    
    
    def set_trigger_state(self, value, return_to_zero_ms=None):
        
        """Sets the current trigger states to an 8-bit value.
        
        Arguments
        
        value               -   Unsigned 8-bit integer value, i.e. an int
                                between 0 and 255. Passing anything else, even
                                a float, will result in an Exception.
        
        Keyword Arguments
        
        return_to_zero_ms   -   Value (int or float) that indicates how long
                                to wait before returning the trigger value
                                to 0. None can be passed to not reset to 0
                                automatically, but instead to return straight
                                after setting the trigger value. Default = None
        
        Returns
        
        t0, t1 t2           -   t0 is the time of this function being called.
                                t1 is the time of the trigger being sent
                                t2 is the time of the 0 trigger being sent,
                                or None if return_to_zero_ms==None.
                                t1 and t2 are clocked directly after the write
                                function returns, in seconds (time.time)
        """
        
        # Start time.
        t0 = time.time()
        
        # Input sanity checks.
        if value < 0 or value > 255 or type(value) != int:
            raise Exception("ERROR: Invalid value '%s' (type=%s); please use an unsigned 8-bit integer!" \
                % (value, type(value)))
        
        # Create a new Task to listen in on the button channels.
        with nidaqmx.Task() as task:
            # Add the digital output (do) channels.
            task.do_channels.add_do_chan("%s/%s" % \
                (self._dev_name, self._trigger_channels))
            # Write a single sample to each channel.
            task.write(value, timeout=0.1)
            t1 = time.time()
        
            # Pause if requested.
            if return_to_zero_ms is not None:
                time.sleep(return_to_zero_ms/1000.0)
                task.write(0, timeout=0.1)
                t2 = time.time()
            else:
                t2 = None
        
        return t0, t1, t2
    
    
    def wait_for_button_press(self, allowed=None, timeout=None):
        
        """Waits for a button press.
        
        Keyword Arguments
        
        allowed             -   List of strings with allowed button names, or
                                None to allow all buttons. Default = None
        
        timeout             -   Float or int that indicates the timeout in
                                seconds. If no button is pressed within the
                                timeout, this function will return. The
                                timeout can be None, meaning no timeout will
                                occur. Default = None
        
        Returns

        button, time        -   button is a string that indicates the pressed
                                button's name (only the first-pressed button
                                is counted), or None if no button was pressed
                                before a timeout occured.
                                time is a float value that reflects the time
                                in seconds at the time the button press was
                                detected.
        """
        
        # Get the indices of the allowed buttons.
        if allowed is not None:
            allow = []
            for b in allowed:
                if b not in self._button_list:
                    raise Exception("ERROR: Unknown button '%s'; available buttons: %s" \
                        % (b, self._button_list))
                allow.append(self._button_list.index(b))
        else:
            allow = range(len(self._button_list))
        
        # Wait for all allowed buttons to be up.
        self._wait_for_button_up(buttons=allow)

        # Get the starting time.
        t0 = time.time()
        t1 = time.time()
        
        # Create a new Task to listen in on the button channels. Using a with
        # statement will automatically close the Task if an error happens
        # during execution, leaving the NI box in a better state.
        with nidaqmx.Task() as task:

            # Add the digital input (di) channels.
            task.di_channels.add_di_chan( \
                "%s/%s" % (self._dev_name, self._button_channels), \
                line_grouping=LineGrouping.CHAN_PER_LINE)
            # Start the task (this will reduce timing inefficience when
            # calling the task.read function).
            task.start()

            # Run until a timeout or a button press occurs.
            button = None
            pressed = False
            timed_out = False
            while not pressed and not timed_out:

                # Get a single sample from the digital input channels.
                state = task.read(number_of_samples_per_channel=1, \
                    timeout=0.001)
                # Get a timestamp for the sample.
                t1 = time.time()

                # Check whether any of the allowed buttons were pressed.
                for i in allow:
                    if state[i][0]:
                        pressed = True
                        button = self._button_list[i]
                        break
                
                # Check whether a timeout occurred.
                if timeout is not None:
                    timed_out = t1 - t0 < timeout
            
            # Stop the task.
            task.stop()
                
        return button, t1
    
    
    def _wait_for_button_up(self, buttons=None):
        
        """Helper function that returns when all or selected are up, i.e. when
        their channel states are False.
        
        Arguments
        
        buttons             -   List of ints that represent indices within
                                the internal list of buttons, or None to
                                select all buttons.
        """
        
        if buttons is None:
            buttons = range(len(self._button_list))
        
        # Create a new Task to listen in on the button channels. Using a with
        # statement will automatically close the Task if an error happens
        # during execution, leaving the NI box in a better state.
        with nidaqmx.Task() as task:

            # Add the digital input (di) channels.
            task.di_channels.add_di_chan( \
                "%s/%s" % (self._dev_name, self._button_channels), \
                line_grouping=LineGrouping.CHAN_PER_LINE)
            # Start the task (this will reduce timing inefficience when
            # calling the task.read function).
            task.start()

            # Run until a timeout or a button press occurs.
            pressed = len(buttons)
            while pressed != 0:

                # Get a single sample from the digital input channels.
                state = task.read(number_of_samples_per_channel=1, \
                    timeout=0.001)

                # Check whether any of the allowed buttons were pressed.
                pressed = 0
                for i in buttons:
                    if state[i][0]:
                        pressed += 1
                        break
            
            # Stop the task.
            task.stop()
                
        return True
