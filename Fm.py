import time
import rda5807m
import sys

from machine import Pin, I2C


presets = [  # Preset stations
    10250,
    10050,
]
i_sidx = 0 # Starting at station with index 0

# Initialize i2c bus
i2c = I2C(0, scl=Pin(1), sda=Pin(0))


vol = 3  # Default volume
band = "FMWORLD"

radio = rda5807m.Radio(i2c, presets[i_sidx], vol)
radio.setBand(band)  # Minimum frequency - 87 Mhz, max - 108 Mhz


# Read input from serial
def serial_read():
    #if supervisor.runtime.serial_bytes_available:
    command = input()
    command = command.split(" ")
    cmd = command[0]
    if cmd == "f":
        value = command[1]
        runSerialCommand(cmd, int(value))
    else:
        runSerialCommand(cmd)
    time.sleep(0.3)
    print(">> ", end="")


def runSerialCommand(cmd, value=0):
    # Executes a command
    # Starts with a character, and optionally followed by an integer, if required
    global i_sidx
    global presets
    if cmd == "?":
        print("? help")
        print("+ increase volume")
        print("- decrease volume")
        print("> next preset")
        print("< previous preset")
        print(". scan up ")
        print(", scan down ")
        print("f direct frequency input like  f 10050")
        print("i station status")
        print("s mono/stereo mode")
        print("b bass boost")
        print("u mute/unmute")
        print("r get rssi data")
        print("e softreset chip")
        print("q stops the program")

    # Volume and audio control
    elif cmd == "+":
        v = radio.volume
        if v < 15:
            radio.setVolume(v + 1)
    elif cmd == "-":
        v = radio.volume
        if v > 0:
            radio.setVolume(v - 1)

    # Toggle mute mode
    elif cmd == "u":
        radio.setMute(not radio.mute)
    # Toggle stereo mode
    elif cmd == "s":
        radio.setMono(not radio.mono)
    # Toggle bass boost
    elif cmd == "b":
        radio.setBassBoost(not radio.bassBoost)

    # Frequency control
    elif cmd == ">":
        # Goes to the next preset station
        if i_sidx < (len(presets) - 1):
            i_sidx = i_sidx + 1
            radio.setFreq(presets[i_sidx])
    elif cmd == "<":
        # Goes to the previous preset station
        if i_sidx > 0:
            i_sidx = i_sidx - 1
            radio.setFreq(presets[i_sidx])

    # Set frequency
    elif cmd == "f":
        radio.setFreq(value)

    # Seek up/down
    elif cmd == ".":
        radio.seekUp()
    elif cmd == ",":
        radio.seekDown()

    # Display current signal strength
    elif cmd == "r":
        print("RSSI: " + str(radio.getRssi()))

    # Soft reset chip
    elif cmd == "e":
        radio.softReset()

    # Not in help
    elif cmd == "!":
        radio.term()
    # Not in help
    elif cmd == "q":
        sys.exit()
    # Exit command
    elif cmd == "i":
        # Display chip info
        s = radio.formatFreq()
        print("Station: " + s)
        print("\nRadio info: ")
        print("RDS -> " + str(radio.rds))
        print("TUNED -> " + str(radio.tuned))
        print("STEREO -> " + str(not radio.mono))
        print("RSSI -> " + str(radio.getRssi()))
        print("\nAudio info: ")
        print("BASS -> " + str(radio.bassBoost))
        print("MUTE -> " + str(radio.mute))
        print("SOFTMUTE -> " + str(radio.softMute))
        print("VOLUME -> " + str(radio.volume))
        

runSerialCommand("?", 0)

print(">> ", end="")

while True:
    serial_read()