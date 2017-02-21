#!/usr/bin/env python
import sys
import time
import serial
from audio_analyzer import *

print "beginning send.py"

arduino = serial.Serial('COM3', 115200)
  # For communicating with the computer, use one of these rates: 
  # 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, or 115200.
serial.Serial.flush(arduino)

numLEDs = 21

def main():
  # spec = SpectrumAnalyzer() # using 32 bins (must be power of 2?)
  # spec.daemon = True
  # spec.start()
  
  rgbs = getRGBs()
  print rgbs
  print len(rgbs)

  while True:
    #rgbs = spec.getRGBs()

    arduino.write(rgbs)
    serial.Serial.flush(arduino)
    time.sleep(.05)

def getRGBs():
  rgbs = []
  for i in range(0, numLEDs):
    rgbs.append([chr(0), chr(0), chr(255)])
  rgbs[4] = [chr(255), chr(0), chr(0)]
  sig = ''.join(''.join(rgb) for rgb in rgbs)+'f'
  return chr(len(sig))+sig

if __name__ == '__main__':
  main()

