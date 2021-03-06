#!/usr/bin/env python

# n bar Audio equaliser using MCP2307
 
import alsaaudio as aa
from time import sleep
from struct import unpack
import numpy as np

import threading


class SpectrumAnalyzer(threading.Thread):

   data_in = aa.PCM(aa.PCM_CAPTURE, aa.PCM_NORMAL)

   sample_rate = 44100
   no_channels = 2
   chunk = 512 # Use a multiple of 8

   bins = 32

   rgbs = []


   def run(self):
      self.main()

   def main(self):
      self.setup()

      while True:
         self.rgbs = self.capture()
         if self.rgbs: print self.rgbs

         sleep(0.001)
         self.data_in.pause(0) # Resume capture

   def capture(self):
      # Read data from device   
      l,data = self.data_in.read()
      self.data_in.pause(1) # Pause capture whilst RPi processes data
      if l:
         # catch frame error
         matrix = self.calculate_levels(data)
         matrix = list(map(self.ampToChr, matrix))
         return ''.join(matrix)

   def ampToChr(self, amp):
      amp = (1<<amp)-1
      if amp < 0:
        return chr(0)
      elif amp > 255:
         return chr(255)
      else:
         return chr(amp)

   def setup(self):
      # Set up audio
      self.data_in.setchannels(self.no_channels)
      self.data_in.setrate(self.sample_rate)
      self.data_in.setformat(aa.PCM_FORMAT_S16_LE)
      self.data_in.setperiodsize(self.chunk)

   def calculate_levels(self, data):
      # Convert raw data to numpy array
      data = unpack("%dh"%(len(data)/2),data)
      data = np.array(data, dtype='h')
      # Apply FFT - real data so rfft used
      fourier = np.fft.rfft(data)
      # Remove last element in array to make it the same size as chunk
      fourier = np.delete(fourier,len(fourier)-1)
      # Find amplitude
      power = np.log10(np.abs(fourier))**2
      # Arange array into self.bin number of rows for the self.bin number of bars on LED matrix
      power = np.reshape(power, (self.bins, self.chunk/self.bins))
      matrix = np.int_(np.average(power,axis=1)/4)
      return matrix

   def getRGBs(self):
      return self.rgbs

print "Processing....."
