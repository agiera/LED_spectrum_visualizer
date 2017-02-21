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


// starts communication with computer and initializes LED strip
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


// get data from computer and display on LED strip and repeat
void loop() 
{
  int ret = getColors();
  if (ret > 0) {
    //successfully read one strips worth of colors
    processSig(ret);
    strip.show();
  }
}


// reads data from computer
int getColors()
{
  if (Serial.available() > 0) {
    
    // the computer tells the arduino how long the message will be
    int ret = Serial.read();
  
    // stores data and discards data that overflows buffer
    // if you want the data and your arduino has room increase BUFF
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


// expands data to look nice on LED strip and sets the colors
void processSig(int ret) {
  int seg = NLEDS/ret;
  for (int i = 0; i < ret; i++) {
    for (int j = 0; j < seg; j++) {
      strip.setPixelColor(i*seg+j, strip.Color(0, 0, sig[i]));
    }
  }
}




