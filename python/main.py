#!/usr/bin/env python
# coding=utf-8

"""
    File name: main.py
    Author: Daniel Fernau
    Date created: 05/05/2018
    Date last modified: 05/21/2018
    Python Version: 2.7
"""

from __future__ import division  # enable "true division"

import serial  # pyserial module
import mido  # mido library
import time
import argparse

# command line arguments
cmdOptions = argparse.ArgumentParser()

cmdOptions.add_argument("-f", "--file", dest="filename",
                        help="midi file", metavar="FILE")
cmdOptions.add_argument("-c", "--console", dest="console",
                        help="output byte arrays to console, and not to serial device(s)", action="store_true")
cmdOptions.add_argument("-1", "--first", dest="arduino1path",
                        help="serial device path of first arduino")
cmdOptions.add_argument("-2", "--second", dest="arduino2path",
                        help="serial device path of second arduino")

options = cmdOptions.parse_args()

# check command line arguments
if not options.filename:
    cmdOptions.error('Filename required!')

if not options.arduino1path and not options.console:
    cmdOptions.error('First tty device path cannot be undefined, unless "-c" flag is present')

# connect to the Arduino boards
if options.arduino1path:
    arduino1 = serial.Serial(options.arduino1path, 9600)
if options.arduino2path:
    arduino2 = serial.Serial(options.arduino2path, 9600)


# function used for communication with the Arduino boards
#   drive_id    -   [ int ]     the number of the disk drive to control (1 - 16)
#   note        -   [ int ]     MIDI note byte as integer (0 - 127)
#   cycles1     -   [ int ]     byte 1 of 2 used to send 'note cycles' value to the board
#   cycles2     -   [ int ]     byte 2 of 2 used to send 'note cycles' value to the board
#   stop        -   [ int ]     used to stop the selected drive (0 = false / 1 = true)
def controller(drive_id, note, cycles1, cycles2, stop):
    # send messages to the first controller attached to drives 1 to 8
    if options.arduino1path:
        if 1 <= drive_id <= 8:
            arduino1.write(bytearray([drive_id, cycles1, cycles2, stop]))

    # send messages to the second controller attached to drives 9 to 16
    if options.arduino2path:
        if 9 <= drive_id <= 16:
            arduino2.write(bytearray([drive_id - 8, cycles1, cycles2, stop]))

    # print messages to the console if the '-c' command line argument is used
    if options.console:
        print(drive_id, note, cycles1, cycles2, stop)

    # save new status
    if stop == 1:
        driveActive[drive_id - 1] = False
    elif stop == 0:
        driveActive[drive_id - 1] = True

    # save new note
    driveNote[drive_id - 1] = note


# array used to convert MIDI note bytes to delay between pulses in 1/10 milliseconds
#   for example:
#   > the C-2 note has a frequency of 65.406 hz, which translates to one pulse every 15.289 milliseconds
#   > (f = 1 / T) --> (65.406 hz = 1 / T) --> (1 / 65.406 hz = 0.015289 s) --> (0.015289 s = 15.289 ms ≈ 15.3 ms)
#   > this means that we need to use a value of 153 * 100 microseconds = 15.3 milliseconds to play the C-2 note
#
#   the reason for [x * 100 µs] is that one cycle of the timer on the Arduino boards is set to 100 microseconds
#
#   the index of the values inside the array equals the MIDI note bytes, which are in the range of 0 to 127
midiByteToCycles = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # C-1 to B-1 -- not used

    612, 577, 545, 514, 485, 458, 432, 408, 385, 364, 343, 324,  # C0 to B0 -- in x * 100 microseconds
    306, 289, 272, 257, 243, 229, 216, 204, 193, 182, 172, 162,  # C1 to B1 -- in x * 100 microseconds
    153, 144, 136, 129, 121, 115, 108, 102, 96, 91, 86, 81,  # C2 to B2 -- in x * 100 microseconds
    76, 72, 68, 64, 61, 57, 54, 51, 48, 45, 43, 40,  # C3 to B3 -- in x * 100 microseconds
    38, 36, 34, 32, 30, 0, 0, 0, 0, 0, 0,  # C4 to E4 -- in x * 100 microseconds

    #  -- cycles with less than 3 milliseconds (3000 microseconds) do not sound very nice on most floppy drives

    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # C5 to B5 -- not used
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # C6 to B6 -- not used
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # C7 to B7 -- not used
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # C8 to B8 -- not used
    0, 0, 0, 0, 0, 0, 0, 0  # C9 to G9 -- not used
]

# the main app
#   I'm using a try...except block to allow clean KeyboardInterrupt handling.
#   If the main process is being interrupted all drives will receive a message to stop playback.
#   This ensures that the drives don't continue playing their last received note forever.
try:
    mid = mido.MidiFile(options.filename)  # load midi file

    # initialize the arrays used to keep track of the playback data
    channelPitch = [0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0]
    channelPitchCycles1 = [0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0]
    channelPitchCycles2 = [0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0]
    driveActive = [False, False, False, False, False, False, False, False,
                   False, False, False, False, False, False, False, False]
    driveNote = [0, 0, 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0, 0, 0]

    time.sleep(3)  # wait three seconds to allow the Arduino boards to finish their initialization

    # Read the midi file - one message at a time:
    for msg in mid:
        time.sleep(msg.time)  # wait specified time before processing the message

        if not msg.is_meta:  # only process non-meta messages
            # Handle 'note_on' events
            if msg.type == 'note_on':
                # Transpose all notes from octave
                #   >   -1  up to   +1
                #   >   ±0  up to   +1
                #   >   +4  down to +3
                #   >   +5  down to +3
                #   >   +6  down to +3:
                if 0 <= msg.note <= 11:
                    msg.note += 24

                if 12 <= msg.note <= 23:
                    msg.note += 12

                if 60 <= msg.note <= 71:
                    msg.note -= 12

                if 72 <= msg.note <= 83:
                    msg.note -= 24

                if 84 <= msg.note <= 95:
                    msg.note -= 36

                # Convert the MIDI note byte to the timer cycles as specified in the 'midiByteToCycles' array:
                midiNoteInCycles = midiByteToCycles[msg.note]

                # Apply the corresponding pitch to the note:
                #   > if the value is below 0 we need to calculate a 'pitch down',
                #   > if the value is larger than 0, we need to calculate a 'pitch up'.
                #
                #   The pitch value covers a range of two semi-tones in each direction.
                #   This is represented by a value between 1 and 8192 for 'pitch up'
                #   as well as values between -1 and -1892 for 'pitch down'.
                #
                #   For 'pitch down' we can use:
                #       (('two semi-tones below' + 'current note') / 8192 * 'absolute value of last pitch message')
                #
                #   and for 'pitch up' we use the equation in the other direction:
                #       (('current note' - 'two semi-tones above') / 8192 * 'absolute value of last pitch message')
                if channelPitch[msg.channel] < 0:
                    notePitchInCycles = ((midiByteToCycles[msg.note - 2] + midiNoteInCycles) / 8192) \
                                        * abs(channelPitch[msg.channel])
                else:
                    notePitchInCycles = ((midiNoteInCycles - midiByteToCycles[msg.note + 2]) / 8192) \
                                        * abs(channelPitch[msg.channel])

                # Now we know how many cycles need to be added or subtracted from the 'normal' note
                # and can calculate the note with pitch in 100µs-timer-cycles:
                midiNoteWithPitchInCycles = midiNoteInCycles + notePitchInCycles

                # Since we can only represent integers between 0 and 127 with one byte,
                # we need to split our '100µs-timer-cycles' value into two parts.
                #
                # This can be achieved by division and the use of the modulo operator:
                #
                # for example:
                #   153 / 10 = int(15.3) = 15
                # and
                #   153 mod 10 = 3
                #
                # The two values are both in the range that can be represented as a byte.
                # Both bytes are being 'put back together' by the code running on the Arduino boards.
                midiNoteCycles1 = int(midiNoteWithPitchInCycles / 10)
                midiNoteCycles2 = int(midiNoteWithPitchInCycles % 10)

                # If the note's velocity is greater than 0 play the note, otherwise stop the drive
                if msg.velocity > 0:
                    # avoid sending more messages to an already active drive:
                    if not driveActive[msg.channel]:
                        # call the 'controller' function with all required data
                        controller(msg.channel + 1, msg.note, midiNoteCycles1, midiNoteCycles2, 0)
                    # print a message if the drive's already busy playing a note and console output is enabled
                    elif options.console:
                        print("drive " + str(msg.channel + 1) + " busy, note skipped")
                # The note's velocity is 0, which means that the drive needs to be stopped:
                else:
                    # call the 'controller' function with '1' as last parameter
                    controller(msg.channel + 1, msg.note, midiNoteCycles1, midiNoteCycles2, 1)

        # Handle 'pitchwheel' events
        if msg.type == 'pitchwheel':
            # Extract the pitch value from the MIDI message and save it to the channelPitch array:
            midiNotePitch = int(str(msg).split()[2].split('=')[1])
            channelPitch[msg.channel] = midiNotePitch

            # Calculate the corresponding pitch as explained above:
            noteBase = driveNote[msg.channel]
            noteBaseInCycles = midiByteToCycles[noteBase]

            if midiNotePitch < 0:
                notePitchInCycles = ((midiByteToCycles[noteBase - 2] - noteBaseInCycles) / 8192) \
                                    * abs(midiNotePitch)
            else:
                notePitchInCycles = ((noteBaseInCycles - midiByteToCycles[noteBase + 2]) / 8192) \
                                    * abs(midiNotePitch)

            noteWithPitchInCycles = int(noteBaseInCycles + notePitchInCycles)
            pitchNoteCycles1 = int(noteWithPitchInCycles / 10)
            pitchNoteCycles2 = int(noteWithPitchInCycles % 10)

            # Check if the drive is active and the pitch has changed;
            #   if yes, apply the new pitch:
            if driveActive[msg.channel] and \
                    (
                            (channelPitchCycles1[msg.channel] != pitchNoteCycles1)
                            or
                            (channelPitchCycles2[msg.channel] != pitchNoteCycles2)
                    ):
                # print message to console, if enabled
                if options.console:
                    print('channel ' + str(msg.channel) + ' pitch changed: ',
                          channelPitchCycles1[msg.channel],
                          channelPitchCycles2[msg.channel],
                          ' => ', pitchNoteCycles1, pitchNoteCycles2)

                # save channel pitch values
                channelPitchCycles1[msg.channel] = pitchNoteCycles1
                channelPitchCycles2[msg.channel] = pitchNoteCycles2

                # update the drive
                controller(msg.channel + 1, noteBase, pitchNoteCycles1, pitchNoteCycles2, 0)

            # if drive is inactive, print 'pitch unchanged' message to console (if enabled)
            elif options.console:
                print('channel ' + str(msg.channel + 1) + ' update skipped, pitch unchanged')

# handle KeyboardInterrupt exception
except KeyboardInterrupt:
    print("KeyboardInterrupt received, stopping...")

# wait one second and then send a 'stop' message to all drives:
time.sleep(1)
for drive in range(1, 17):
    controller(drive, 0, 0, 0, 1)
    time.sleep(0.1)
