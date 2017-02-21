// This arduino program reads in colors from PORT
// and lights accordingly.
// To light up the strip write the rgb as chars to the 
// arduino for every led starting with the first.

// WARNING: the RX buffer in `arduino-x.x.x/hardware/arduino/avr/cores/arduino/HardwareSerial.h`
// must be greater than NLEDS * 3

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>

#define PIN 6
#define NLEDS 150

int getColors(); // recieves colors from computer and stores locally

unsigned char rgb[NLEDS][3]; // nLEDs amount of R/G/B values [in decimal]
int ret = 0;

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NLEDS, PIN, NEO_GRB + NEO_KHZ800);



void setup() 
{
  memset(rgb, 0, sizeof rgb);
  
  Serial.begin(57600);
  
  strip.begin();
  strip.show();
}

void loop() 
{
  ret = getColors();
  if (ret == 0) {
    //successfully read one strips worth of colors
    for (int i = 0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, strip.Color(rgb[i][0], rgb[i][1], rgb[i][2]));
    }
    strip.show();
  }
}

int getColors()
{
  if (Serial.available() == NLEDS*3) {
    for (int i = 0; i < NLEDS; i++) {
      for (int c = 0; c < 3; c++) {
        rgb[i][c] = Serial.read();
      }
    }
    Serial.flush();
      
    return 0;
  }
  
  return 1;
}

