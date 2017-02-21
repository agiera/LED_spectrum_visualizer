// This arduino program creates cool color patterns and
// displays them on addressable LEDs
// for each led there is a ring that transitions from off to blue to green to red
// they all have the same velocities, but different angular velocities
// this causes them to go in and out of sync over time according to lowest common factors

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>

#define PIN 6
#define NLEDS 150

#define INNERRAD 1
#define INTERVAL .01

const float pi = 3.14159;
float t; //time

void getColors(); // recieves colors from computer and stores locally

unsigned char rgbs[NLEDS][3]; // nLEDs amount of R/G/B values [in decimal]

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NLEDS, PIN, NEO_GRB + NEO_KHZ800);


void setup() 
{
  memset(rgbs, 0, sizeof rgbs);
  
  Serial.begin(115200);
  
  strip.begin();
  strip.show();
}

void loop() 
{
  getColors();
  //successfully read one strips worth of colors
  for (int i = 0; i < NLEDS; i++) {
    strip.setPixelColor(i, strip.Color(rgbs[i][0], rgbs[i][1], rgbs[i][2]));
  }
  strip.show();
}

void getColors()
{
  t = millis()/500.0;
  Serial.println(t);
  float c, s;
  for(int i = 0; i < NLEDS; i++) {
    c = cos(2*pi*INNERRAD*t/(INNERRAD+i*INTERVAL));
    s = sin(2*pi*INNERRAD*t/(INNERRAD+i*INTERVAL));
    if(c > 0) {
      rgbs[i][2] = 255*c;
    } else {
      rgbs[i][0] = -255*c;
    }
    if(s < 0) {
      rgbs[i][1] = -255*s;
    }
  }
}


