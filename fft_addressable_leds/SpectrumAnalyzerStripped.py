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

from time import gmtime, strftime

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
AUDIOdevin = None                       # Audio device for input. None = Windows default
AUDIOdevout = None                      # Audio device for output. None = Windows default
AUDIOlevel = 0.0                        # Level of audio input 0 to 1
AUDIOstatus = 0                         # 0 audio off, 1 audio on

FFTbandwidth = 0                        # The FFT bandwidth
FFTresult = []                          # FFT result
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
    
def AUDIOin():   # Read the audio from the stream and store the data into the arrays
    global AUDIOdevin
    global AUDIOdevout
    global AUDIOsignal1
    global AUDIOstatus
    global RUNstatus
    global RXbuffer
    global RXbufferoverflow
    global SAMPLErate
    global SMPfft
    global UPDATEspeed
    
    while (True):                                           # Main loop
        PA = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16                            # Audio format 16 levels and 2 channels
        CHUNK = int(SMPfft)

        # RUNstatus = 1 : Open Stream
        if (RUNstatus == 1):
            INITIALIZEstart()                               # Initialize variables

            if UPDATEspeed < 1:
                UPDATEspeed = 1.0

            TRACESopened = 1

            try:
                chunkbuffer = CHUNK
                if chunkbuffer < SAMPLErate / 10:           # Prevent buffer overload if small number of samples
                    chunkbuffer = int(SAMPLErate / 10)

                chunkbuffer = int(UPDATEspeed * chunkbuffer)
                
                stream = PA.open(format = FORMAT,
                    channels = TRACESopened, 
                    rate = SAMPLErate, 
                    input = True,
                    output = True,
                    frames_per_buffer = int(chunkbuffer),
                    input_device_index = AUDIOdevin,
                    output_device_index = AUDIOdevout)
                RUNstatus = 2
            except:                                         # If error in opening audio stream, show error
                RUNstatus = 0
                txt = "Sample rate: " + str(SAMPLErate) + ", try a lower sample rate.\nOr another audio device."
                showerror("Cannot open Audio Stream", txt)     

            
        # RUNstatus = 2: Reading audio data from soundcard
        if (RUNstatus == 2):
            buffervalue = stream.get_read_available()       # Buffer reading testroutine
            RXbuffer = 100.0 * float(buffervalue) / chunkbuffer  # Buffer filled in %. Overflow at 2xchunkbuffer
            RXbufferoverflow = False
            try:
                signals = ""
                if buffervalue > chunkbuffer:               # ADDED FOR RASPBERRY PI WITH ALSA, PERHAPS NOT NECESSARY WITH PULSE
                    signals = stream.read(chunkbuffer)      # Read samples from the buffer

                if (AUDIOstatus == 1):                      # Audio on
                        stream.write(signals, chunkbuffer)
            except:
                AUDIOsignal1 = []
                RUNstatus = 4
                RXbufferoverflow = True                     # Buffer overflow at 2x chunkbuffer


            # Conversion audio samples to values -32762 to +32767 (ones complement) and add to AUDIOsignal1
            AUDIOsignal1 = []                               # Clear the AUDIOsignal1 array for trace 1
            AUDIOsignal1.extend(numpy.fromstring(signals, "Int16"))

            UpdateAll()                                     # Update Data, trace and screen



        # RUNstatus = 3: Stop
        # RUNstatus = 4: Stop and restart
        if (RUNstatus == 3) or (RUNstatus == 4):
            stream.stop_stream()
            stream.close()
            PA.terminate()
            if RUNstatus == 3:
                RUNstatus = 0                               # Status is stopped 
            if RUNstatus == 4:          
                RUNstatus = 1                               # Status is (re)start


def UpdateAll():        # Update Data, trace and screen
    global AUDIOsignal1
    global SMPfft

    if len(AUDIOsignal1) < SMPfft:
        return
    
    DoFFT()             # Fast Fourier transformation



def DoFFT():            # Fast Fourier transformation
    global AUDIOsignal1
    global AUDIOlevel
    global FFTmemory
    global FFTresult
    global FFTwindowshape
    global SAMPLErate
    global SMPfft
    global STARTfrequency
    global STOPfrequency
    global TRACEaverage
    global TRACEmode
    global TRACEreset
    global ZEROpadding
    
    T1 = time.time()                        # For time measurement of FFT routine
    
    REX = []
    IMX = []
      

    # Convert list to numpy array REX for faster Numpy calculations
    FFTsignal = AUDIOsignal1[:SMPfft]                       # Take the first fft samples
    REX = numpy.array(FFTsignal)                            # Make a numpy arry of the list


    # Set Audio level display value
    MAXaudio = 16000.0                                      # MAXaudio is 16000 for a normal soundcard, 50% of the total range of 32768
    REX = REX / MAXaudio
    
    MAXlvl = numpy.amax(REX)                                # First check for maximum positive value
    AUDIOlevel = MAXlvl                                     # Set AUDIOlevel

    MINlvl = numpy.amin(REX)                                # Then check for minimum positive value
    MINlvl = abs(MINlvl)                                    # Make absolute
    if MINlvl > AUDIOlevel:
        AUDIOlevel = MINlvl


    # Do the FFT window function
    REX = REX * FFTwindowshape                              # The windowing shape function only over the samples


    # Zero padding of array for better interpolation of peak level of signals
    ZEROpaddingvalue = int(2 ** ZEROpadding)
    fftsamples = ZEROpaddingvalue * SMPfft                  # Add zero's to the arrays

    # Save previous trace in memory for max or average trace
    FFTmemory = FFTresult

    # FFT with numpy 
    ALL = numpy.fft.fft(REX, n=fftsamples)                  # Do FFT + zeropadding till n=fftsamples with NUMPY  ALL = Real + Imaginary part
    ALL = numpy.absolute(ALL)                               # Make absolute SQR(REX*REX + IMX*IMX) for VOLTAGE!
    ALL = ALL * ALL                                         # Convert from Voltage to Power (P = (U*U) / R; R = 1)
    
    le = len(ALL)
    le = le / 2                                             # Only half is used, other half is mirror
    ALL = ALL[:le]                                          # So take only first half of the array
    
    Totalcorr = float(ZEROpaddingvalue)/ fftsamples         # For VOLTAGE!
    Totalcorr = Totalcorr * Totalcorr                       # For POWER!
    FFTresult = Totalcorr * ALL


    if TRACEmode == 1:                                      # Normal mode 1, do not change
        pass

    if TRACEmode == 2 and TRACEreset == False:              # Max hold mode 2, change v to maximum value
        FFTresult = numpy.maximum(FFTresult, FFTmemory)

    if TRACEmode == 3 and TRACEreset == False:              # Average mode 3, add difference / TRACEaverage to v
        FFTresult = FFTmemory + (FFTresult - FFTmemory) / TRACEaverage

    print FFTresult

    TRACEreset = False                                      # Trace reset done

    T2 = time.time()
    # print (T2 - T1)                                         # For time measurement of FFT routine



def INITIALIZEstart():
    global SMPfft
    global SMPfftpwrTwo
    global TRACEreset


    # First some subroutines to set specific variables
    SMPfft = 2 ** int(SMPfftpwrTwo)                         # Calculate the number of FFT samples from SMPfftpwrtwo

    CALCFFTwindowshape()

    TRACEreset = True                                       # Clear the memory for averaging or peak
    

def CALCFFTwindowshape():                       # Make the FFTwindowshape for the windowing function
    global FFTbandwidth                         # The FFT bandwidth
    global FFTwindow                            # Which FFT window number is selected
    global FFTwindowname                        # The name of the FFT window function
    global FFTwindowshape                       # The window shape
    global SAMPLErate                           # The sample rate
    global SMPfft                               # Number of FFT samples
    
    
    # FFTname and FFTbandwidth in milliHz
    FFTwindowname = "No such window"
    FFTbw = 0
    
    if FFTwindow == 0:
        FFTwindowname = "0-Rectangular (no) window (B=1) "
        FFTbw = 1.0

    if FFTwindow == 1:
        FFTwindowname = "1-Cosine window (B=1.24) "
        FFTbw = 1.24

    if FFTwindow == 2:
        FFTwindowname = "2-Triangular window (B=1.33) "
        FFTbw = 1.33

    if FFTwindow == 3:
        FFTwindowname = "3-Hann window (B=1.5) "
        FFTbw = 1.5

    if FFTwindow == 4:
        FFTwindowname = "4-Blackman window (B=1.73) "
        FFTbw = 1.73

    if FFTwindow == 5:
        FFTwindowname = "5-Nuttall window (B=2.02) "
        FFTbw = 2.02

    if FFTwindow == 6:
        FFTwindowname = "6-Flat top window (B=3.77) "
        FFTbw = 3.77

    FFTbandwidth = int(1000.0 * FFTbw * SAMPLErate / float(SMPfft)) 

    # Calculate the shape
    FFTwindowshape = numpy.ones(SMPfft)         # Initialize with ones

    # m = 0                                       # For calculation of correction factor, furhter no function

    n = 0
    while n < SMPfft:

        # Cosine window function
        # medium-dynamic range B=1.24
        if FFTwindow == 1:
            w = math.sin(math.pi * n / (SMPfft - 1))
            FFTwindowshape[n] = w * 1.571

        # Triangular non-zero endpoints
        # medium-dynamic range B=1.33
        if FFTwindow == 2:
            w = (2.0 / SMPfft) * ((SMPfft/ 2.0) - abs(n - (SMPfft - 1) / 2.0))
            FFTwindowshape[n] = w * 2.0

        # Hann window function
        # medium-dynamic range B=1.5
        if FFTwindow == 3:
            w = 0.5 - 0.5 * math.cos(2 * math.pi * n / (SMPfft - 1))
            FFTwindowshape[n] = w * 2.000

        # Blackman window, continuous first derivate function
        # medium-dynamic range B=1.73
        if FFTwindow == 4:
            w = 0.42 - 0.5 * math.cos(2 * math.pi * n / (SMPfft - 1)) + 0.08 * math.cos(4 * math.pi * n / (SMPfft - 1))
            FFTwindowshape[n] = w * 2.381

        # Nuttall window, continuous first derivate function
        # high-dynamic range B=2.02
        if FFTwindow == 5:
            w = 0.355768 - 0.487396 * math.cos(2 * math.pi * n / (SMPfft - 1)) + 0.144232 * math.cos(4 * math.pi * n / (SMPfft - 1))- 0.012604 * math.cos(6 * math.pi * n / (SMPfft - 1))
            FFTwindowshape[n] = w * 2.811

        # Flat top window, 
        # medium-dynamic range, extra wide bandwidth B=3.77
        if FFTwindow == 6:
            w = 1.0 - 1.93 * math.cos(2 * math.pi * n / (SMPfft - 1)) + 1.29 * math.cos(4 * math.pi * n / (SMPfft - 1))- 0.388 * math.cos(6 * math.pi * n / (SMPfft - 1)) + 0.032 * math.cos(8 * math.pi * n / (SMPfft - 1))
            FFTwindowshape[n] = w * 1.000
        
        # m = m + w / SMPfft                          # For calculation of correction factor
        n = n + 1

    # if m > 0:                                     # For calculation of correction factor
    #     print "correction 1/m: ", 1/m             # For calculation of correction factor



def SELECTaudiodevice():        # Select an audio device
    global AUDIOdevin
    global AUDIOdevout

    PA = pyaudio.PyAudio()
    ndev = PA.get_device_count()

    n = 0
    ai = ""
    ao = ""
    while n < ndev:
        s = PA.get_device_info_by_index(n)
        # print n, s
        if s['maxInputChannels'] > 0:
            ai = ai + str(s['index']) + ": " + s['name'] + "\n"
        if s['maxOutputChannels'] > 0:
            ao = ao + str(s['index']) + ": " + s['name'] + "\n"
        n = n + 1
    PA.terminate()

    AUDIOdevin = None
    
    s = raw_input("Select audio INPUT device:\nPress Cancel for Windows Default\n\n" + ai + "\n\nNumber: ")
    if (s != None):             # If Cancel pressed, then None
        try:                    # Error if for example no numeric characters or OK pressed without input (s = "")
            v = int(s)
        except:
            s = "error"

        if s != "error":
            if v < 0 or v > ndev:
                v = 0
            AUDIOdevin = v

    AUDIOdevout = None

    s = raw_input("Select audio OUTPUT device:\nPress Cancel for Windows Default\n\n" + ao + "\n\nNumber: ")
    if (s != None):             # If Cancel pressed, then None
        try:                    # Error if for example no numeric characters or OK pressed without input (s = "")
            v = int(s)
        except:
            s = "error"

        if s != "error":
            if v < 0 or v > ndev:
                v = 0
            AUDIOdevout = v




# start----------------------------------------------------------------

SELECTaudiodevice()
AUDIOin()
 


