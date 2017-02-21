#!/usr/bin/env python

# n bar Audio equaliser using MCP2307

import pyaudio
from time import sleep
from struct import unpack
import numpy as np
import math

import threading


class SpectrumAnalyzer(threading.Thread):

	pa = pyaudio.PyAudio()
	
	sample_rate = 44100
	no_channels = 2
	chunk = 1024 # Use a multiple of 8

	bins = 32

	rgbs = []


	def run(self):
		self.main()

	def main(self):
		self.setup()

		while True:
			self.rgbs = self.capture()

		sleep(0.001)
		self.data_in.pause(0) # Resume capture

	def capture(self):
		# Read data from device
		if self.data_in.get_read_available():
			data = self.data_in.read(self.chunk)
			# catch frame error
			matrix = self.calculate_levels(data)
			print matrix
			matrix = list(map(self.ampToChr, matrix))
			return ''.join(matrix)

	def ampToChr(self, amp):
		if amp < 0:
			return chr(0)
		elif amp > 255:
			return chr(255)
		else:
			return chr(amp)

	def setup(self):
		# Set up audio
		self.data_in = self.pa.open(format=pyaudio.paInt16,channels=self.no_channels, \
                            rate=self.sample_rate,input=True,frames_per_buffer=int(self.chunk))

	def calculate_levels(self, data):
		# Convert raw data to numpy array
		data = unpack("%dh"%(len(data)/2),data)
		data = np.array(data, dtype='h')

		# if you take an FFT of a chunk of audio, the edges will look like
		# super high frequency cutoffs. Applying a window tapers the edges
		# of each end of the chunk down to zero.
		window = np.hanning(len(data))
		data = data * window

		# Apply FFT - real data so rfft used
		fourier = np.fft.rfft(data)

		# Remove last element in array to make it the same size as chunk
		fourier = np.delete(fourier,len(fourier)-1)

		# Find amplitude
		power = np.log10(np.abs(fourier))**2*8
		# # Scale to make it look nice
		# x = 2.0;
		# y = 2.0;
		# for i in range(0, power.size):
			# power[i] = power[i]*(math.log(x)/y)
			# x += x

		# Arange array into self.bin number of rows for the self.bin number of bars on LED matrix
		power = np.reshape(power, (self.bins, self.chunk/self.bins))
		matrix = np.int_(np.average(power,axis=1)/4)

		return matrix

	def getRGBs(self):
		return self.rgbs

print "Processing....."
