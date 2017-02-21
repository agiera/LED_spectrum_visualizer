import ddf.minim.analysis.*;
import ddf.minim.*;
import processing.serial.*; 
 
Serial arduino;
 
Minim minim;
AudioInput in;
FFT fft;

int buffer_size = 4096; 
float sample_rate = 200000;

int freq_width = 250; // <-O-> set the frequency range for each band over 400hz. larger bands will have less intensity per band. smaller bands would result in the overall range being limited

//arrays to hold the 64 bands' data
float[] freq_height;

byte[] sig;

void setup()
{
  size(200, 200);

  minim = new Minim(this);
  //arduino = new Serial(this, "/dev/ttyUSB0" , 9600); // set baud rate and port
 
  in = minim.getLineIn(Minim.MONO,buffer_size,sample_rate);
 
  // create an FFT object that has a time-domain buffer 
  // the same size as line-in's sample buffer
  fft = new FFT(in.bufferSize(), in.sampleRate());
  // Tapered window important for log-domain display
  fft.window(FFT.HAMMING);
}


void draw()
{
  // perform a forward FFT on the samples in input buffer
  fft.forward(in.mix);
  
  
  freq_height[0] = fft.calcAvg((float) 0, (float) 30);
  freq_height[1] = fft.calcAvg((float) 31, (float) 60);
  freq_height[2] = fft.calcAvg((float) 61, (float) 100);
  freq_height[3] = fft.calcAvg((float) 101, (float) 150);
  freq_height[4] = fft.calcAvg((float) 151, (float) 200);
  freq_height[5] = fft.calcAvg((float) 201, (float) 250);
  freq_height[6] = fft.calcAvg((float) 251, (float) 300);
  freq_height[7] = fft.calcAvg((float) 301, (float) 350);
  freq_height[8] = fft.calcAvg((float) 351, (float) 400);
  
  for (int n = 9; n < 64; n++) {
    freq_height[n] = fft.calcAvg((float) (351+(freq_width*(n-9))), (float) (500+(freq_width*(n-9))));
  }
  
  
  // Log scaling function. Feel free to adjust x and y
  
  float x = 8;
  float y = 3;
  for (int i = 0; i < 64; i++) {    
    freq_height[i] = freq_height[i]*(log(x)/y);
    x += x;
  }
  

   

  // safely convert amplitudes into streamable data
  for(int i = 0; i < 64; i++){    
    if (freq_height[i] > 255) {
      sig[i] = byte(255);
    } else if (freq_height[i] < 0) {
      sig[i] = byte(0);
    } else {
      sig[i] = byte(int(freq_height[i]));
    }
  }
  
  // send data
  //arduino.write(sig);
}
 
 
void stop()
{
  // always close Minim audio classes when you finish with them
  in.close();
  minim.stop();
 
  super.stop();
}
