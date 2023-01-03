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
from MidiNoteToFreq import *

led = machine.Pin(25,machine.Pin.OUT)


# trendline for 440Hz base cassette follow y = ax+b
trendline_a = -0.0092
trendline_b = 11.553

# trendline for 440Hz base cassette follow y = ax+b
trendline220_a = -0.0092
trendline220_b = 9.522

# which MIDI note number corresponds to 0V CV
lowest_note = 40;

# create gate pin
gate = machine.Pin(17, machine.Pin.OUT)
gate.value(0)

# safe button
safe_button = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)


#create an I2C bus
sda_philips=machine.Pin(6)
scl_philips=machine.Pin(7)
i2c_to_philips = machine.I2C(1, scl=scl_philips, sda=sda_philips, freq=400000)

sda_cv=machine.Pin(4)
scl_cv=machine.Pin(5)
i2c_cv = machine.I2C(0, scl=scl_cv, sda=sda_cv, freq=400000)

# calculate 1mV: steps / max V / 1000
mv = 4096 / 5.1 / 1000

# calculate mV per semitone
semitone = 83.33 * mv

last_dac_value = 0

# DAC function
def writeToDacPhilips(value):
    buf=bytearray(2)
    buf[0]=(value >> 8) & 0xFF
    buf[1]=value & 0xFF
    i2c_to_philips.writeto(0x62,buf)
    
def writeToDacCv(value):
    buf=bytearray(2)
    buf[0]=(value >> 8) & 0xFF
    buf[1]=value & 0xFF
    i2c_cv.writeto(0x62,buf)
# Initialise the serial MIDI handling
uart = machine.UART(0,31250)

# MIDI callback routines
def doMidiNoteOn(ch, cmd, note, vel):
    global semitone, last_dac_value, trendline_a, trendline_b
    
    # simple cv output
    writeToDacCv(int((note-lowest_note)*semitone))
    gate.value(1)
    
    # cv for the philips tape player
    freq_new_note = midi_note_to_freq[note]
    voltage_new_note = trendline_a*freq_new_note+trendline_b
    new_dac_value = int(voltage_new_note/10*4095)
    
    if new_dac_value > 4095:
        new_dac_value = 4095
    elif new_dac_value < 1000:
        new_dac_value = 1000
        
    print("doMidiNoteOn", ch, cmd, note, vel, "output voltage : ", (new_dac_value)/4095*10)
    for i in range(last_dac_value, new_dac_value, 5 if new_dac_value>last_dac_value else -5):
        writeToDacPhilips(i)
    
    writeToDacPhilips(new_dac_value)
    last_dac_value = new_dac_value

def doMidiNoteOff(ch, cmd, note, vel):
    print("doMidiNoteOff", ch, cmd, note, vel)
    global semitone
    gate.value(0)

# initialise MIDI decoder and set up callbacks
md = SimpleMIDIDecoder.SimpleMIDIDecoder()
md.cbNoteOn (doMidiNoteOn)
md.cbNoteOff (doMidiNoteOff)

led.high()
time.sleep(0.1)   
led.low()
time.sleep(0.1)   
led.high()

if safe_button.value() == 1:
    print("begin")
    # the loop
    while True:
        # Check for MIDI messages
        if (uart.any()):
            md.read(uart.read(1)[0])
else:
    print("safe button pressed at boot, will quit software")
