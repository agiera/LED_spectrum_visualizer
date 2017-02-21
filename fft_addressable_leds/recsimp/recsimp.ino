// This arduino program reads in colors from PORT
// and lights accordingly.
// To light up the strip write the rgb as chars to the 
// arduino for every led starting with the first.

// WARNING:
// The RX buffer in `arduino-x.x.x/hardware/arduino/avr/cores/arduino/HardwareSerial.h`
// must be greater than signal size.

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>
#include <math.h>

#define PIN 6
#define NLEDS 150
#define BUFF 512

int mode;
int strobe = 0;
float period = 1;
int velocity;
unsigned char colors[3][7]; //limits amount of fade colors
int colorlen;

unsigned long pixelcount = 0;
int ret;
unsigned char sig[BUFF];

void updateSettings(void);
int getSig(void); // recieves signal from computer and processes cmd into colors
void fade(void);
void wave(void);
void equalizerFade(int);
void equalizerStack(int);
void ambiance(int);

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NLEDS, PIN, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel stripOff = Adafruit_NeoPixel(NLEDS, PIN, NEO_GRB + NEO_KHZ800);


// starts communication with computer and initializes LED strip
void setup() 
{
  Serial.begin(115200);
  /*
  For communicating with the computer, use one of these rates: 
  300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, or 115200.
  */
  
  // initiate communication
  Serial.write((char) 199);
  Serial.flush();

  // setup LEDs
  strip.begin();
  strip.show();
  stripOff.begin();
  stripOff.show();

  while (Serial.available() <= 0) {delay(10);}
  if (Serial.read() != (unsigned char)(211)) {
    while (1) {delay(100);}
  }
  
  // program sets mode
  updateSettings();

  // tell program we're all set up
  Serial.write((char) 223);
  Serial.flush();
}

/*
0: fade : frequency of strobe and list of colours
1: wave : frequency of strobe, frequency of wave, and list of colours
3: equalizer : list of four colours
4: wave equalizer: list of colours
*/
void updateSettings()
{
  while (Serial.available() <= 0) {delay(10);}
  delay(100);
  int len = Serial.available();
  mode = Serial.read();
  switch (mode)
  {
    case 0:
      strobe = Serial.read();
      period = Serial.read()/10.0;
      colorlen = (len-3)/3;
      for (int i = 0; i < colorlen; i++) {
        colors[0][i] = Serial.read();
        colors[1][i] = Serial.read();
        colors[2][i] = Serial.read();
      }
      break;
    case 1:
      strobe = Serial.read();
      period = Serial.read();
      velocity = Serial.read();
      colorlen = (len-4)/3;
      for (int i = 0; i < colorlen; i++) {
        colors[0][i] = Serial.read();
        colors[1][i] = Serial.read();
        colors[2][i] = Serial.read();
      }
      break;
    case 2:
      colorlen = (len-1)/3;
      for (int i = 0; i < colorlen; i++) {
        colors[0][i] = Serial.read();
        colors[1][i] = Serial.read();
        colors[2][i] = Serial.read();
      }
      break;
    case 3:
      velocity = Serial.read();
      colorlen = (len-2)/3;
      for (int i = 0; i < colorlen; i++) {
        colors[0][i] = Serial.read();
        colors[1][i] = Serial.read();
        colors[2][i] = Serial.read();
      }
      break;
    case 4:
      break;
    default:
      colorlen = 3;
      colors[0][0] = 255;
      colors[1][1] = 255;
      colors[2][2] = 255;
      mode = 0;
  }
}


// get data from computer and display on LED strip and repeat
void loop() 
{
  doStrobe();
  switch (mode)
  {
    case 0:
      fade();
      strip.show();
      break;
    case 1:
      wave();
      strip.show();
      break;
    case 2:
      ret = getSig();
      if (ret > 0) {
        //successfully read one strips worth of colors
        equalizerFade(ret);
        strip.show();
      }
      break;
    case 3:
      ret = getSig();
      if (ret >= 0) {
        //successfully read one strips worth of colors
        equalizerStack(ret);
        strip.show();
      }
      break;
    case 4:
      ret = getSig();
      if (ret >= 0) {
        //successfully read one strips worth of colors
        ambiance(ret);
        strip.show();
      }
      break;
    default:
      break;
  }
}




// reads data from computer
int getSig()
{
  if (Serial.available() > 0) {
    
    // the computer tells the arduino how long the message will be
    unsigned int ret = Serial.read();
  
    // stores data and discards data that overflows buffer
    // if you want the data and your arduino has room increase BUFF
    for (int i = 0; i < ret; i++) {
      while (Serial.available() <= 0);
      if (i >= BUFF) {
        Serial.read();
      } else {
        sig[i] = Serial.read();
      }
    }
    
    if (ret > BUFF) {ret = BUFF;}

    delay(5);
    // tells computer its ready for more data
    Serial.write((char) ret);
    Serial.flush();
  
    return ret;
  }
  return 0;
}


void doStrobe()
{
  // for every one milis with light on three is spent off
  if (strobe > 0 && millis() % (1000 / strobe) > 1000/(float)(strobe)/4.0) {
    stripOff.show();
    delay((int)(3000/(float)(strobe)/4.0));
    strip.show();
  }
}



void fade()
{
  float mod = (millis() % (int)(period * colorlen * 1000))/1000.0;
  int i1 = mod / period;
  float c = mod / period - i1;
  int i2 = (i1 + 1) % colorlen;
  int r = colors[0][i1]*(1-c) + colors[0][i2]*c;
  int g = colors[1][i1]*(1-c) + colors[1][i2]*c;
  int b = colors[2][i1]*(1-c) + colors[2][i2]*c;
  for (int i = 0; i < NLEDS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
}

void wave()
{
  if (pixelcount < millis()/1000.0 * velocity) {
    int i1 = (pixelcount % ((int)(period) * colorlen)) / period;
    int i2 = (i1 + 1) % colorlen;
    float c = (pixelcount % ((int)(period) * colorlen)) / period - i1;
    int r = colors[0][i1]*cos(c*PI/2) + colors[0][i2]*sin(c*PI/2);
    int g = colors[1][i1]*cos(c*PI/2) + colors[1][i2]*sin(c*PI/2);
    int b = colors[2][i1]*cos(c*PI/2) + colors[2][i2]*sin(c*PI/2);
    for (int i = NLEDS-1; i > 0; i--) {
      strip.setPixelColor(i, strip.getPixelColor(i-1));
    }
    strip.setPixelColor(0, strip.Color(r, g, b));
    pixelcount++;
  }
}


// expands data to look nice on LED strip and sets the colors
//void equalizer(int ret)
//{
//  int seg = NLEDS/ret;
//  int r, g, b;
//  for (int i = 0; i < ret; i++) {
////    b = 3*sig[i] > 255 ? 0 : 255-3*sig[i];
////    g = 3*sig[i] > 2*255 ? 2*255-3*sig[i] : (3*sig[i] > 255 ? 3*sig[i]-255 : 0);
////    r = 3*sig[i] > 2*255 ? 3*sig[i]-2*255 : 0;
//    b = 4*sig[i] > 2*255 ? 2*255-4*sig[i] : (4*sig[i] > 255 ? 4*sig[i]-255 : 0);
//    g = 4*sig[i] > 3*255 ? 3*255-4*sig[i] : (4*sig[i] > 2*255 ? 4*sig[i]-2*255 : 0);
//    r = 4*sig[i] > 3*255 ? 4*sig[i]-3*255 : 0;
//    for (int j = 0; j < seg; j++) {
//      strip.setPixelColor(i*seg+j, strip.Color(r, g, b));
//    }
//  }
//}

void equalizerFade(int ret)
{
  float mod = (millis() % (int)(period * colorlen * 1000))/1000.0;
  int i1 = mod / period;
  float c = mod / period - i1;
  int i2 = (i1 + 1) % colorlen;
  int r = colors[0][i1]*(1-c) + colors[0][i2]*c;
  int g = colors[1][i1]*(1-c) + colors[1][i2]*c;
  int b = colors[2][i1]*(1-c) + colors[2][i2]*c;
  for (int i = 0; i < NLEDS; i++) {
    strip.setPixelColor(i, strip.Color((sig[i]*r)/256, (sig[i]*g)/256, (sig[i]*b)/256));
  }
}


//void waveEqualizer(int height)
//{
//  while (pixelcount < millis()/1000.0 * velocity) {
//    int sudoperiod = 500/height;
//    int i1 = (pixelcount % (sudoperiod * colorlen)) / sudoperiod;
//    int i2 = (i1 + 1) % colorlen;
//    float c = (pixelcount % (sudoperiod * colorlen)) / sudoperiod - i1;
//    int r = colors[0][i1]*cos(c*PI/2) + colors[0][i2]*sin(c*PI/2);
//    int g = colors[1][i1]*cos(c*PI/2) + colors[1][i2]*sin(c*PI/2);
//    int b = colors[2][i1]*cos(c*PI/2) + colors[2][i2]*sin(c*PI/2);
//    for (int i = NLEDS-1; i > 0; i--) {
//      strip.setPixelColor(i, strip.getPixelColor(i-1));
//    }
//    strip.setPixelColor(0, strip.Color(r, g, b));
//    pixelcount++;
//  }
//}

void equalizerStack(int ret)
{
  for (int i = 0; i < NLEDS; i++) {
    int i1 = sig[i] * colorlen / 256;
    float c = sig[i] * colorlen / 256.0 - i1;
    int i2 = (i1 + 1) % colorlen;
    int r = colors[0][i1]*(1-c) + colors[0][i2]*c;
    int g = colors[1][i1]*(1-c) + colors[1][i2]*c;
    int b = colors[2][i1]*(1-c) + colors[2][i2]*c;
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
}

void ambiance(int ret)
{
  for (int i = 0; i < NLEDS*3; i++) {
    strip.setPixelColor(i, strip.Color(sig[i*3], sig[i*3+1], sig[i*3+2]));
  }
}

