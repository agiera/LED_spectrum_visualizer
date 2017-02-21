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
  
    return ret;
  }
  return 0;
}

void processSig(int ret) {

  for (int i = 0; i < ret; i++) {
    Serial.print(int(sig[i]));
    Serial.print(",");
  }
  Serial.println(ret);


  int seg = NLEDS/ret;
  for (int i = 0; i < ret; i++) {
    for (int j = 0; j < seg; j++) {
      strip.setPixelColor(i*seg+j, strip.Color(0, 0, sig[i]));
    }
  }
}



