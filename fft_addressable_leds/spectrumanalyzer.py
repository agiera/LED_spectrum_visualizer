# SpectrumAnalyzer-v02a.py(w)  (15-03-2015)
# For Python version 2.6 or 2.7
# With external module pyaudio (for Python version 2.6 or 2.7); NUMPY module (for used Python version)
# Created by Onno Hoekstra (pa2ohh)
import pyaudio
import math
import time
import wave
import struct
import numpy.fft
import threading

from time import gmtime, strftime



class SpectrumAnalyzer(threading.Thread):

    # Values that can be modified
    SAMPLErate = 48000                      # Sample rate of the sound system 24000 48000 96000 192000

    TRACEmode = 1                           # 1 normal mode, 2 max hold mode, 3 average mode
    TRACEaverage = 10                       # Number of average sweeps for average mode
    TRACEreset = True                       # True for first new trace, reset max hold and averageing 
    UPDATEspeed = 1.1                       # Update speed can be increased when problems if PC too slow, default 1.1
    ZEROpadding = 1                         # ZEROpadding for signal interpolation between frequency samples (0=none)



    # Initialisation of general variables
    STARTfrequency = 0.0                    # Startfrequency
    STOPfrequency = 10000.0                 # Stopfrequency
    ZEROpadding = 1                         # The zero padding value is 2 ** ZERO padding, calculated on initialize

                           
    # Other global variables required in various routines
    AUDIOsignal1 = []                       # Audio trace channel 1
    AUDIOlevel = 0.0                        # Level of audio input 0 to 1
    AUDIOstatus = 0                         # 0 audio off, 1 audio on

    FFTbandwidth = 0                        # The FFT bandwidth
    FFTresult = []                          # FFT result
    FFTfinal = []                           # as to not interfere with hyperthreading
    FFTwindow = 5                           # FFTwindow 0=None (rectangular B=1), 1=Cosine (B=1.24), 2=Triangular non-zero endpoints (B=1.33),
                                            # 3=Hann (B=1.5), 4=Blackman (B=1.73), 5=Nuttall (B=2.02), 6=Flat top (B=3.77)
    FFTwindowname = "--"                    # The FFT window name
    FFTmemory = numpy.ones(1)               # The memory for averaging

    RUNstatus = 1                           # 0 stopped, 1 start, 2 running, 3 stop now, 4 stop and restart
    RXbuffer = 0.0                          # Data contained in input buffer in %
    RXbufferoverflow = False

    SMPfftpwrTwo = 11                       # The power of two of SMPfft
    SMPfft = 2 ** SMPfftpwrTwo              # Initialize



    # ============================================ Main routine ====================================================

    def run(self):
        self.AUDIOin()

    def AUDIOin(self):   # Read the audio from the stream and store the data into the arrays
        while (True):                                           # Main loop
            PA = pyaudio.PyAudio()
            CHUNK = int(self.SMPfft)

            # RUNstatus = 1 : Open Stream
            if (self.RUNstatus == 1):
                self.INITIALIZEstart()                               # Initialize variables

                if self.UPDATEspeed < 1:
                    self.UPDATEspeed = 1.0

                try:
                    chunkbuffer = CHUNK
                    if chunkbuffer < self.SAMPLErate / 10:           # Prevent buffer overload if small number of samples
                        chunkbuffer = int(self.SAMPLErate / 10)

                    chunkbuffer = int(self.UPDATEspeed * chunkbuffer)

                    stream = PA.open(format=pyaudio.paInt16,channels=1,\
                                     rate=self.SAMPLErate,input=True,frames_per_buffer=int(chunkbuffer))
                    self.RUNstatus = 2
                except:                                         # If error in opening audio stream, show error
                    self.RUNstatus = 0
                    txt = "Sample rate: " + str(self.SAMPLErate) + ", try a lower sample rate.\nOr another audio device."
                    showerror("Cannot open Audio Stream", txt)     

                
            # RUNstatus = 2: Reading audio data from soundcard
            if (self.RUNstatus == 2):
                buffervalue = stream.get_read_available()       # Buffer reading testroutine
                self.RXbuffer = 100.0 * float(buffervalue) / chunkbuffer  # Buffer filled in %. Overflow at 2xchunkbuffer
                self.RXbufferoverflow = False
                try:
                    signals = ""
                    if buffervalue > chunkbuffer:               # ADDED FOR RASPBERRY PI WITH ALSA, PERHAPS NOT NECESSARY WITH PULSE
                        signals = stream.read(chunkbuffer)      # Read samples from the buffer

                    if (self.AUDIOstatus == 1):                      # Audio on
                            stream.write(signals, chunkbuffer)
                except:
                    self.AUDIOsignal1 = []
                    self.RUNstatus = 4
                    self.RXbufferoverflow = True                     # Buffer overflow at 2x chunkbuffer


                # Conversion audio samples to values -32762 to +32767 (ones complement) and add to AUDIOsignal1
                self.AUDIOsignal1 = []                               # Clear the AUDIOsignal1 array for trace 1
                self.AUDIOsignal1.extend(numpy.fromstring(signals, "Int16"))

                self.UpdateAll()                                     # Update Data, trace and screen



            # RUNstatus = 3: Stop
            # RUNstatus = 4: Stop and restart
            if (self.RUNstatus == 3) or (self.RUNstatus == 4):
                stream.stop_stream()
                stream.close()
                PA.terminate()
                if self.RUNstatus == 3:
                    self.RUNstatus = 0                               # Status is stopped 
                if self.RUNstatus == 4:          
                    self.RUNstatus = 1                               # Status is (re)start


    def UpdateAll(self):        # Update Data, trace and screen
        if len(self.AUDIOsignal1) < self.SMPfft:
            return
        
        self.DoFFT()             # Fast Fourier transformation



    def DoFFT(self):            # Fast Fourier transformation
        T1 = time.time()                        # For time measurement of FFT routine
        
        REX = []
        IMX = []
          

        # Convert list to numpy array REX for faster Numpy calculations
        FFTsignal = self.AUDIOsignal1[:self.SMPfft]                       # Take the first fft samples
        REX = numpy.array(FFTsignal)                            # Make a numpy arry of the list


        # Set Audio level display value
        MAXaudio = 16000.0                                      # MAXaudio is 16000 for a normal soundcard, 50% of the total range of 32768
        REX = REX / MAXaudio
        
        MAXlvl = numpy.amax(REX)                                # First check for maximum positive value
        self.AUDIOlevel = MAXlvl                                     # Set AUDIOlevel

        MINlvl = numpy.amin(REX)                                # Then check for minimum positive value
        MINlvl = abs(MINlvl)                                    # Make absolute
        if MINlvl > self.AUDIOlevel:
            self.AUDIOlevel = MINlvl


        # Do the FFT window function
        REX = REX * self.FFTwindowshape                              # The windowing shape function only over the samples


        # Zero padding of array for better interpolation of peak level of signals
        ZEROpaddingvalue = int(2 ** self.ZEROpadding)
        fftsamples = ZEROpaddingvalue * self.SMPfft                  # Add zero's to the arrays

        # Save previous trace in memory for max or average trace
        self.FFTmemory = self.FFTresult

        # FFT with numpy 
        ALL = numpy.fft.fft(REX, n=fftsamples)                  # Do FFT + zeropadding till n=fftsamples with NUMPY  ALL = Real + Imaginary part
        ALL = numpy.absolute(ALL)                               # Make absolute SQR(REX*REX + IMX*IMX) for VOLTAGE!
        ALL = ALL * ALL                                         # Convert from Voltage to Power (P = (U*U) / R; R = 1)
        
        le = len(ALL)
        le = le / 2                                             # Only half is used, other half is mirror
        ALL = ALL[:le]                                          # So take only first half of the array
        
        Totalcorr = float(ZEROpaddingvalue)/ fftsamples         # For VOLTAGE!
        Totalcorr = Totalcorr * Totalcorr                       # For POWER!
        self.FFTresult = Totalcorr * ALL


        if self.TRACEmode == 1:                                      # Normal mode 1, do not change
            pass

        if self.TRACEmode == 2 and self.TRACEreset == False:              # Max hold mode 2, change v to maximum value
            self.FFTresult = numpy.maximum(self.FFTresult, self.FFTmemory)

        if self.TRACEmode == 3 and self.TRACEreset == False:              # Average mode 3, add difference / TRACEaverage to v
            self.FFTresult = self.FFTmemory + (self.FFTresult - self.FFTmemory) / self.TRACEaverage

        self.FFTfinal = self.FFTresult

        self.TRACEreset = False                                      # Trace reset done

        T2 = time.time()
        # print (T2 - T1)                                         # For time measurement of FFT routine



    def INITIALIZEstart(self):
        # First some subroutines to set specific variables
        self.SMPfft = 2 ** int(self.SMPfftpwrTwo)                         # Calculate the number of FFT samples from SMPfftpwrtwo

        self.CALCFFTwindowshape()

        self.TRACEreset = True                                       # Clear the memory for averaging or peak
        

    def CALCFFTwindowshape(self):                       # Make the FFTwindowshape for the windowing function
        # FFTname and FFTbandwidth in milliHz
        self.FFTwindowname = "No such window"
        FFTbw = 0
        
        if self.FFTwindow == 0:
            self.FFTwindowname = "0-Rectangular (no) window (B=1) "
            FFTbw = 1.0

        if self.FFTwindow == 1:
            self.FFTwindowname = "1-Cosine window (B=1.24) "
            FFTbw = 1.24

        if self.FFTwindow == 2:
            self.FFTwindowname = "2-Triangular window (B=1.33) "
            FFTbw = 1.33

        if self.FFTwindow == 3:
            self.FFTwindowname = "3-Hann window (B=1.5) "
            FFTbw = 1.5

        if self.FFTwindow == 4:
            self.FFTwindowname = "4-Blackman window (B=1.73) "
            FFTbw = 1.73

        if self.FFTwindow == 5:
            self.FFTwindowname = "5-Nuttall window (B=2.02) "
            FFTbw = 2.02

        if self.FFTwindow == 6:
            self.FFTwindowname = "6-Flat top window (B=3.77) "
            FFTbw = 3.77

        self.FFTbandwidth = int(1000.0 * FFTbw * self.SAMPLErate / float(self.SMPfft)) 

        # Calculate the shape
        self.FFTwindowshape = numpy.ones(self.SMPfft)         # Initialize with ones

        # m = 0                                       # For calculation of correction factor, furhter no function

        n = 0
        while n < self.SMPfft:

            # Cosine window function
            # medium-dynamic range B=1.24
            if self.FFTwindow == 1:
                w = math.sin(math.pi * n / (self.SMPfft - 1))
                self.FFTwindowshape[n] = w * 1.571

            # Triangular non-zero endpoints
            # medium-dynamic range B=1.33
            if self.FFTwindow == 2:
                w = (2.0 / self.SMPfft) * ((self.SMPfft/ 2.0) - abs(n - (self.SMPfft - 1) / 2.0))
                self.FFTwindowshape[n] = w * 2.0

            # Hann window function
            # medium-dynamic range B=1.5
            if self.FFTwindow == 3:
                w = 0.5 - 0.5 * math.cos(2 * math.pi * n / (self.SMPfft - 1))
                self.FFTwindowshape[n] = w * 2.000

            # Blackman window, continuous first derivate function
            # medium-dynamic range B=1.73
            if self.FFTwindow == 4:
                w = 0.42 - 0.5 * math.cos(2 * math.pi * n / (self.SMPfft - 1)) + 0.08 * math.cos(4 * math.pi * n / (self.SMPfft - 1))
                self.FFTwindowshape[n] = w * 2.381

            # Nuttall window, continuous first derivate function
            # high-dynamic range B=2.02
            if self.FFTwindow == 5:
                w = 0.355768 - 0.487396 * math.cos(2 * math.pi * n / (self.SMPfft - 1)) + 0.144232 * math.cos(4 * math.pi * n / (self.SMPfft - 1))- 0.012604 * math.cos(6 * math.pi * n / (self.SMPfft - 1))
                self.FFTwindowshape[n] = w * 2.811

            # Flat top window, 
            # medium-dynamic range, extra wide bandwidth B=3.77
            if self.FFTwindow == 6:
                w = 1.0 - 1.93 * math.cos(2 * math.pi * n / (self.SMPfft - 1)) + 1.29 * math.cos(4 * math.pi * n / (self.SMPfft - 1))- 0.388 * math.cos(6 * math.pi * n / (self.SMPfft - 1)) + 0.032 * math.cos(8 * math.pi * n / (self.SMPfft - 1))
                self.FFTwindowshape[n] = w * 1.000
            
            # m = m + w / SMPfft                          # For calculation of correction factor
            n = n + 1

        # if m > 0:                                     # For calculation of correction factor
        #     print "correction 1/m: ", 1/m             # For calculation of correction factor


    def spectrumToRGBs(self, numLEDs):
        if len(self.FFTfinal) < numLEDs*3: return chr(0)
        rgbs = self.FFTfinal[:numLEDs*3]
        rgbs = [self.ampToChr(i) for i in rgbs]
        return ''.join(rgbs[:numLEDs*3])

    def ampToChr(self, amp):
        if amp < 0:
            return chr(0)
        elif amp * 10**7 > 255:
            return chr(255)
        else:
            return chr(int(amp * 10**7))
