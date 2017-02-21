// This arduino program reads in colors from PORT
// and lights accordingly.
// To light up the strip write the rgb as chars to the 
// arduino for every led starting with the first.

// WARNING: the RX buffer in `arduino-x.x.x/hardware/arduino/avr/cores/arduino/HardwareSerial.h`
// must be greater than signal size

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>

#define PIN 6
#define BUFF 64
#define NLEDS 150

int getSignal(); // recieves colors from computer and stores locally

unsigned char sig[BUFF]; // nLEDs amount of R/G/B values [in decimal]
int ret = 0;

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NLEDS, PIN, NEO_GRB + NEO_KHZ800);



void setup() 
{
  memset(sig, 0, sizeof sig);
  
  Serial.begin(57600);
  /*
  For communicating with the computer, use one of these rates: 
  300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, or 115200.
  */
  
  strip.begin();
  strip.show();
}

void loop() 
{
  ret = getSignal();
  if (ret > 0) {
    //successfully read a cmd
    int bins = NLEDS/ret;
    int j = 0;
    for(int i = 0; i < ret; i++){
      for(int j = 0; j < NLEDS/ret; j++){
        strip.setPixelColor(i*NLEDS/ret+j, strip.Color(0, 0, sig[i]));
      }
    }
    strip.show();
  }
}

int getSignal()
{
  char ret = Serial.available();
  if (ret > 0) {
    if (ret > BUFF){ret = BUFF;} //prevent buffer overflow

    for (int i = 0; i < ret; i++) {
      sig[i] = Serial.read();
    }

    Serial.flush();
    return ret;
  }
  return 0;
}

