// This arduino program reads in colors from PORT
// and lights accordingly.
// To light up the strip write the rgb as chars to the 
// arduino for every led starting with the first.

// WARNING:
// The RX buffer in `arduino-x.x.x/hardware/arduino/avr/cores/arduino/HardwareSerial.h`
// must be greater than signal size.

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>

#define PIN 6
#define NLEDS 150
#define BUFF 128

int getColors(); // recieves signal from computer and processes cmd into colors

unsigned char sig[BUFF];

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NLEDS, PIN, NEO_GRB + NEO_KHZ800);



void setup() 
{
  
  Serial.begin(115200);
  /*
  For communicating with the computer, use one of these rates: 
  300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, or 115200.
  */
  
  strip.begin();
  strip.show();
  
  // initiate communication
  Serial.write((char) 1);
  Serial.flush();
}

void loop() 
{
  int ret = getColors();
  if (ret > 0) {
    //successfully read one strips worth of colors
    processSig(ret);
    strip.show();
  }
}

int getColors()
{
  if (Serial.available() > 0) {
    
    int ret = Serial.read();
  
    for (int i = 0; i < ret; i++) {
      while (Serial.available() <= 0) {delay(1);}
      if (i >= BUFF) {
        Serial.read();
      } else {
        sig[i] = Serial.read();
      }
    }
    
    if (ret > BUFF) {ret = BUFF;}
    
    // tells computer its ready for more data
    Serial.write((char) ret);
    Serial.flush();
  
    return ret;
  }
  return 0;
}

void processSig(int ret) {
  int seg = NLEDS/ret;
  int r, g, b;
  for (int i = 0; i < ret; i++) {
//    b = 3*sig[i] > 255 ? 0 : 255-3*sig[i];
//    g = 3*sig[i] > 2*255 ? 2*255-3*sig[i] : (3*sig[i] > 255 ? 3*sig[i]-255 : 0);
//    r = 3*sig[i] > 2*255 ? 3*sig[i]-2*255 : 0;
    b = 4*sig[i] > 2*255 ? 2*255-4*sig[i] : (4*sig[i] > 255 ? 4*sig[i]-255 : 0);
    g = 4*sig[i] > 3*255 ? 3*255-4*sig[i] : (4*sig[i] > 2*255 ? 4*sig[i]-2*255 : 0);
    r = 4*sig[i] > 3*255 ? 4*sig[i]-3*255 : 0;
    for (int j = 0; j < seg; j++) {
      strip.setPixelColor(i*seg+j, strip.Color(r, g, b));
    }
  }
}




