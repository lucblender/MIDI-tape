# MIDI to CV converter for Raspberry Pi Pico and MCP4725 DAC by @AxWax
#
# Demo: https://www.youtube.com/watch?v=aGfQHL1jU4I
#
# This is heavily based on and requires
# the SimpleMIDIDecoder library by @diyelectromusic, which can be found at
# https://diyelectromusic.wordpress.com/2021/06/13/raspberry-pi-pico-midi-channel-router/
#
#
# Wiring:
# serial midi input on GP1 (UART0 RX)
# gate output: GP17
#
# MCP4725   Pico
# GND       GND
# VCC       VBUS (5V)
# SDA       GP6
# SCL       GP7
# VOUT is the CV output

import machine
import time
import ustruct
import SimpleMIDIDecoder

# which MIDI note number corresponds to 0V CV
lowest_note = 40;

# create gate pin
gate = machine.Pin(17, machine.Pin.OUT)
gate.value(0)

#create an I2C bus
sda=machine.Pin(6)
scl=machine.Pin(7)
i2c = machine.I2C(1, scl=scl, sda=sda, freq=400000)

# calculate 1mV: steps / max V / 1000
mv = 4096 / 5.1 / 1000

# calculate mV per semitone
semitone = 83.33 * mv

# DAC function
def writeToDac(value):
    buf=bytearray(2)
    buf[0]=(value >> 8) & 0xFF
    buf[1]=value & 0xFF
    i2c.writeto(0x62,buf)

# Initialise the serial MIDI handling
uart = machine.UART(0,31250)

# MIDI callback routines
def doMidiNoteOn(ch, cmd, note, vel):
    global semitone
    writeToDac(int((note-lowest_note)*semitone))
    gate.value(1)

def doMidiNoteOff(ch, cmd, note, vel):
    global semitone
    gate.value(0)

# initialise MIDI decoder and set up callbacks
md = SimpleMIDIDecoder.SimpleMIDIDecoder()
md.cbNoteOn (doMidiNoteOn)
md.cbNoteOff (doMidiNoteOff)

# the loop
while True:
    # Check for MIDI messages
    if (uart.any()):
        md.read(uart.read(1)[0])
