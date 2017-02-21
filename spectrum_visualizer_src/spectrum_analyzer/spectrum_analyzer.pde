import ddf.minim.analysis.*;
import ddf.minim.*;
import processing.serial.*;
import java.util.Arrays;
import java.util.List;

import controlP5.*;

import java.awt.GraphicsEnvironment;
import java.awt.GraphicsDevice;
import java.awt.DisplayMode;
import java.awt.Rectangle;
import java.awt.image.BufferedImage;
import java.awt.AWTException;
import java.awt.Robot;


final String curDir = System.getProperty("user.dir");


//gui global vars
ControlP5 controlP5;
DropdownList dropSetting;
Textlabel portLabel;
Textfield strobeField;
Textfield periodField;
Textfield velocityField;
Textfield scalarField;
Textfield delayField;
Textlabel redLabel;
Textlabel greenLabel;
Textlabel blueLabel;
ArrayList<Textlabel> colorLabels = new ArrayList<Textlabel>();
ArrayList<ArrayList<Textfield>> colorsFields = new ArrayList<ArrayList<Textfield>>();
int numColors = 1;
Button subColor;
Button addColor;
Button start;
Button stop;

String[] modes = {"fade", "wave", "equalizer fade", "equalizer stack", "ambiance"};
int mode = 0;


// audio processing global vars
Serial arduino;
String conn = "disconnected";
 
Minim minim;
AudioInput in;
FFT fft;
boolean runAnalyzer = false;

int bins = 150;  // this code only supports a max of 255
                 // with modification you could probably increase it

int buffer_size = 4096; 
float sample_rate = 200000;

int max_freq = 2000;

//arrays to hold the 64 bands' data
float[] freq_height = new float[bins];
float[] pivot = new float[bins];

float delay = 4;

//amplitudes scalar
float c = 64.0;

byte[] sig = new byte[bins+1];

int count = 0;


//screen processesing
boolean runAmbiance = false;

void setup()
{
  // setup gui
  size(220, 400);
  controlP5 = new ControlP5(this);
  
  portLabel = controlP5.addTextlabel("port", "port: " + conn, 20, 20);
  portLabel.setColor(color(255));
  
  strobeField = controlP5.addTextfield("strobe (Hz)", 20, 80, 50, 20);
  strobeField.setText("0");
  strobeField.hide();
  
  periodField = controlP5.addTextfield("period (PXs/color)", 100, 80, 50, 20);
  periodField.setText("0");
  periodField.hide();
  
  delayField = controlP5.addTextfield("height subtracted per .1 seconds", 20, 80, 50, 20);
  delayField.setText("255");
  delayField.hide();
  
  velocityField = controlP5.addTextfield("velocity (PXs/sec)", 100, 120, 50, 20);
  velocityField.setText("50");
  velocityField.hide();
  
  scalarField = controlP5.addTextfield("volume scalar", 20, 120, 50, 20);
  scalarField.setText("64");
  scalarField.hide();
  
  redLabel = controlP5.addTextlabel("redLabel", "red", 74, 165);
  greenLabel = controlP5.addTextlabel("greenLabel", "green", 120, 165);
  blueLabel = controlP5.addTextlabel("blueLabel", "blue", 173, 165);
  
  for (int i = 0; i < 7; i++) {
    colorLabels.add(controlP5.addTextlabel("color" + (i+1), "color "+(i+1)+":", 20, 185 + i*25));
    colorLabels.get(i).hide();
    colorsFields.add(new ArrayList<Textfield>());
    colorsFields.get(i).add(controlP5.addTextfield("red"  + (i+1), 70, 180 + i*25, 30, 20));
    colorsFields.get(i).get(0).setText("255").getCaptionLabel().setVisible(false);
    colorsFields.get(i).get(0).hide();
    colorsFields.get(i).add(controlP5.addTextfield("green" + (i+1), 120, 180 + i*25, 30, 20));
    colorsFields.get(i).get(1).setText("255").getCaptionLabel().setVisible(false);
    colorsFields.get(i).get(1).hide();
    colorsFields.get(i).add(controlP5.addTextfield("blue" + (i+1), 170, 180 + i*25, 30, 20));
    colorsFields.get(i).get(2).setText("255").getCaptionLabel().setVisible(false);
    colorsFields.get(i).get(2).hide();
  }
  colorLabels.get(0).show();
  colorsFields.get(0).get(0).show();
  colorsFields.get(0).get(1).show();
  colorsFields.get(0).get(2).show();
  
  subColor = controlP5.addButton("  -", 0, 20, 360, 20, 20);
  addColor = controlP5.addButton("  +", 1, 40, 360, 20, 20);
  start = controlP5.addButton("        start", 2, 80, 360, 60, 20);
  stop = controlP5.addButton("        stop", 2, 140, 360, 60, 20);
  
  dropSetting = controlP5.addDropdownList("mode select", 20, 60, 100, 120);
  customize(dropSetting);
  
  
  File file = new File(curDir + "settings.conf");
  if (!file.exists()) {
    String[] initialState = {"<state>", "number of LEDs: 150", "mode: 0", 
                             "fade:", "\tstrobe: 0", "\tperiod: 10", "\tr1: 255", "\tg1: 255", "\tb1: 255", 
                             "wave:", "\tstrobe: 0", "\tperiod: 10", "\tvelocity: 50", "\tr1: 255", "\tg1: 255", "\tb1: 255", 
                             "equalizer fade:", "\tscalar: 8", "\tdelay: 16", "\tr1: 255", "\tg1: 255", "\tb1: 255", 
                             "equalizer stack:", "\tscalar: 64", "\tdelay: 255", "\tr1: 255", "\tg1: 255", "\tb1: 255", "</ state>"};
    saveStrings("settings.conf", initialState);
  }
  loadState();
  
  
  //connects to default recording device
  minim = new Minim(this);
  in = minim.getLineIn(Minim.MONO,buffer_size,sample_rate);
 
  // create an FFT object that has a time-domain buffer 
  // the same size as line-in's sample buffer
  fft = new FFT(in.bufferSize(), in.sampleRate());
  // Tapered window important for log-domain display
  fft.window(FFT.HAMMING);
}


void customize(DropdownList ddl) {
  ddl.setBackgroundColor(color(190));
  ddl.setItemHeight(20);
  //ddl.setBarHeight(20);
  //ddl.captionLabel().set("mode select");
  //ddl.captionLabel().style().marginTop = 5;
  ////ddl.captionLabel().style().marginLeft = 3;
  //ddl.valueLabel().style().marginTop = 3;
  for (int i = 0; i < modes.length; i++){
    ddl.addItem(modes[i], i);
  }
  ddl.setColorBackground(color(60));
  ddl.setColorActive(color(255, 128));
}

// this functions listens to events and can act upon it
void controlEvent(ControlEvent theEvent) {
  // if the event is from a group, which is the case with the dropdownlist
  if (theEvent.isGroup()) {
    // if the name of the event is equal to ImageSelect (aka the name of our dropdownlist)
    if (theEvent.group().name() == dropSetting.getName()) {
      // then do stuff, in this case: set the variable selectedImage to the value associated
      // with the item from the dropdownlist (which in this case is either 0 or 1)
      mode = int(theEvent.group().value());
      loadHelper();
    }
  } else if(theEvent.isController()) {
    if (theEvent.controller().name() == subColor.getName()) {
      if (numColors > 1) {
        subColor();
      }
    } else if (theEvent.controller().name() == addColor.getName()) {
      if (numColors < 7) {
        addColor();
      }
    } else if (theEvent.controller().name() == start.getName()) {
      saveState();
      restart();
    } else if (theEvent.controller().name() == stop.getName()) {
      halt();
    }
  }
}

//this function updates the text boxes to customize each mode
void updateGUI(int mode) {
  switch (mode) {
    case 0:
      scalarField.hide();
      delayField.hide();
      velocityField.hide();
      strobeField.show();
      periodField.show();
      periodField.setLabel("period (decisecs/color)");
      redLabel.show();
      greenLabel.show();
      blueLabel.show();
      subColor.show();
      addColor.show();
      break;
    case 1:
      scalarField.hide();
      delayField.hide();
      strobeField.show();
      velocityField.show();
      periodField.show();
      periodField.setLabel("period (PXs/color)");
      redLabel.show();
      greenLabel.show();
      blueLabel.show();
      subColor.show();
      addColor.show();
      break;
    case 2:
      strobeField.hide();
      periodField.hide();
      velocityField.hide();
      scalarField.show();
      delayField.show();
      redLabel.show();
      greenLabel.show();
      blueLabel.show();
      subColor.show();
      addColor.show();
      break;
    case 3:
      strobeField.hide();
      periodField.hide();
      scalarField.show();
      delayField.show();
      velocityField.hide();
      redLabel.show();
      greenLabel.show();
      blueLabel.show();
      subColor.show();
      addColor.show();
      break;
    case 4:
      //hide everything
      strobeField.hide();
      periodField.hide();
      scalarField.hide();
      delayField.hide();
      velocityField.hide();
      subColor.hide();
      addColor.hide();
      redLabel.hide();
      greenLabel.hide();
      blueLabel.hide();
      while (numColors > 0) {subColor();}
      break;
    default:
      print("This should never happen");
  }
}

void addColor() {
  // show new line
  colorLabels.get(numColors).show();
  colorsFields.get(numColors).get(0).show();
  colorsFields.get(numColors).get(1).show();
  colorsFields.get(numColors).get(2).show();
  
  numColors++;
}

void subColor() {
  numColors--;
  
  // hide prev line
  colorLabels.get(numColors).hide();
  colorsFields.get(numColors).get(0).hide();
  colorsFields.get(numColors).get(1).hide();
  colorsFields.get(numColors).get(2).hide();
}

void loadState() {
  ArrayList<String> lines = new ArrayList(Arrays.asList(loadStrings("settings.conf")));
  mode = Integer.parseInt(lines.get(2).split(": ")[1]);
  dropSetting.setValue(mode);
}

// this is called every time dropSetting value is set
void loadHelper() {
  ArrayList<String> lines = new ArrayList(Arrays.asList(loadStrings("settings.conf")));
  int i = lines.indexOf(modes[mode] + ":")+1;
  switch (mode) {
    case 0:
      strobeField.setText(lines.get(i++).split(": ")[1]);
      periodField.setText(lines.get(i++).split(": ")[1]);
      break;
    case 1:
      strobeField.setText(lines.get(i++).split(": ")[1]);
      periodField.setText(lines.get(i++).split(": ")[1]);
      velocityField.setText(lines.get(i++).split(": ")[1]);
      break;
    case 2:
      scalarField.setText(lines.get(i++).split(": ")[1]);
      delayField.setText(lines.get(i++).split(": ")[1]);
      break;
    case 3:
      scalarField.setText(lines.get(i++).split(": ")[1]);
      delayField.setText(lines.get(i++).split(": ")[1]);
      break;
    case 4:
      // this mode has no settings
      updateGUI(mode);
      return;
    default:
      print("This should never happen.");
  }
  int c;
  for (c = 0; lines.get(i+3*c).contains("\t"); c++) {
    for (int j = 0; j < 3; j++) {
      colorsFields.get(c).get(j).setText(lines.get(i+3*c+j).split(": ")[1]);
    }
  }
  // changing the number of colors on the screen to match loading info
  while (c > numColors) {addColor();}
  while (c < numColors) {subColor();}
  updateGUI(mode);
}

// if file does not exist one will be created at start of program
// sanatizes data inputs
void saveState() {
  // update existing state
  List<String> lines = new ArrayList(Arrays.asList(loadStrings("settings.conf")));
  lines.set(2, "mode: " + mode);
  if (mode == 4) {
    // mode 4 has no settings
    saveStrings("settings.conf", lines.toArray(new String[lines.size()]));
    return;
  }
  int i = lines.indexOf(modes[mode] + ":")+1;
  while (lines.get(i).contains("\t")) {
    lines.remove(i);
  }
  //I put things in backward so i wouldn't have to iterate i, sorry
  for (int j = numColors-1; j >= 0; j--) {
    colorsFields.get(j).get(2).setText(sanatize(colorsFields.get(j).get(2).getText()));
    colorsFields.get(j).get(1).setText(sanatize(colorsFields.get(j).get(1).getText()));
    colorsFields.get(j).get(0).setText(sanatize(colorsFields.get(j).get(0).getText()));
    lines.add(i, "\tb" + (j+1) + ": " + colorsFields.get(j).get(2).getText());
    lines.add(i, "\tg" + (j+1) + ": " + colorsFields.get(j).get(1).getText());
    lines.add(i, "\tr" + (j+1) + ": " + colorsFields.get(j).get(0).getText());
  }
  switch (mode) {
    case 0:
      periodField.setText(sanatize(periodField.getText()));
      strobeField.setText(sanatize(strobeField.getText()));
      lines.add(i, "\tperiod: " + periodField.getText());
      lines.add(i, "\tstrobe: " + strobeField.getText());
      break;
    case 1:
      velocityField.setText(sanatize(velocityField.getText()));
      periodField.setText(sanatize(periodField.getText()));
      strobeField.setText(sanatize(strobeField.getText()));
      lines.add(i, "\tvelocity: " + velocityField.getText());
      lines.add(i, "\tperiod: " + periodField.getText());
      lines.add(i, "\tstrobe: " + strobeField.getText());
      break;
    case 2:
      delayField.setText(sanatize(delayField.getText()));
      scalarField.setText(sanatize(scalarField.getText()));
      c = Integer.parseInt(scalarField.getText());
      delay = Integer.parseInt(delayField.getText());
      lines.add(i, "\tdelay: " + delayField.getText());
      lines.add(i, "\tscalar: " + scalarField.getText());
      break;
    case 3:
      velocityField.setText(sanatize(velocityField.getText()));
      delayField.setText(sanatize(delayField.getText()));
      scalarField.setText(sanatize(scalarField.getText()));
      c = Integer.parseInt(scalarField.getText());
      delay = Integer.parseInt(delayField.getText());
      lines.add(i, "\tdelay: " + delayField.getText());
      lines.add(i, "\tscalar: " + scalarField.getText());
      break;
    case 4:
      break;
    default:
      print("This should never happen.");
  }
  saveStrings("settings.conf", lines.toArray(new String[lines.size()]));
}

// converts any string into a byte and then converts back to string
String sanatize(String val) {
  try {
    int ival = Integer.parseInt(val);
    if (ival < 0) {
      return "0";
    } else if (ival > 255) {
      return "255";
    } else {
      return Integer.toString(ival);
    }
  } catch  (NumberFormatException e) {
    // not an integer!
    return "0";
  }
}



void restart() {
  connArduino();
  byte[] modeSig;
  switch (mode) {
    case 0:
      modeSig = new byte[3+numColors*3];
      modeSig[0] = (byte) mode;
      modeSig[1] = ampToChar(Integer.parseInt(strobeField.getText()));
      modeSig[2] = ampToChar(Integer.parseInt(periodField.getText()));
      for (int i = 0; i < numColors; i++) {
        modeSig[3+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(0).getText()));
        modeSig[4+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(1).getText()));
        modeSig[5+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(2).getText()));
      }
      break;
    case 1:
      modeSig = new byte[4+numColors*3];
      modeSig[0] = (byte) mode;
      modeSig[1] = ampToChar(Integer.parseInt(strobeField.getText()));
      modeSig[2] = ampToChar(Integer.parseInt(periodField.getText()));
      modeSig[3] = ampToChar(Integer.parseInt(velocityField.getText()));
      for (int i = 0; i < numColors; i++) {
        modeSig[4+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(0).getText()));
        modeSig[5+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(1).getText()));
        modeSig[6+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(2).getText()));
      }
      break;
    case 2:
      modeSig = new byte[1+numColors*3];
      modeSig[0] = (byte) mode;
      for (int i = 0; i < numColors; i++) {
        modeSig[1+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(0).getText()));
        modeSig[2+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(1).getText()));
        modeSig[3+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(2).getText()));
      }
      runAnalyzer = true;
      break;
    case 3:
      modeSig = new byte[1+numColors*3];
      modeSig[0] = (byte) mode;
      for (int i = 0; i < numColors; i++) {
        modeSig[1+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(0).getText()));
        modeSig[2+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(1).getText()));
        modeSig[3+i*3] = ampToChar(Integer.parseInt(colorsFields.get(i).get(2).getText()));
      }
      runAnalyzer = true;
      break;
    case 4:
      modeSig = new byte[1];
      modeSig[0] = (byte) mode;
      runAmbiance = true;
      break;
    default:
      modeSig = new byte[0];
      println("This should never happen.");
  }
  if (conn != "disconnected") {
    arduino.write(modeSig);
  }
  delay(100);
}

void halt() {
  connArduino();
  if (arduino != null) {
    arduino.stop();
  }
}



void connArduino() {
  runAnalyzer = false;
  runAmbiance = false;
  if (arduino != null) {
    arduino.stop();
  }
  /*
  For communicating with the computer, use one of these rates: 
  300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, or 115200.
  */
  for (int i = 0; i < Serial.list().length; i++) {
    arduino = new Serial(this, Serial.list()[i], 115200); // set baud rate and port
    delay(4000); // arduino takes about 3 sec to restart and send init message
    if (arduino.read() == 199) {
      conn = Serial.list()[i];
      arduino.write((byte)(211));
      break;
    }
  }
  delay(100);
  portLabel.setText("port: " + conn);
}






void draw()
{
  // refreshes background so things don't overlap
  background(0);
  
  // Sends audio information to arduino
  if (runAnalyzer) {
    runSpectrumAnalyzer();
  }
  if (runAmbiance) {
    sendAmbiance();
  }
}


void runSpectrumAnalyzer()
{
  // perform a forward FFT on the samples in input buffer
  fft.forward(in.mix);
  

  // starting at smaller intervals to larger
  pivot[0] = fft.calcAvg((float) 0, (float) 14);
  pivot[1] = fft.calcAvg((float) 15, (float) 29);
  pivot[2] = fft.calcAvg((float) 30, (float) 44);
  pivot[3] = fft.calcAvg((float) 45, (float) 59);
  pivot[4] = fft.calcAvg((float) 60, (float) 89);
  pivot[5] = fft.calcAvg((float) 90, (float) 119);
  pivot[6] = fft.calcAvg((float) 120, (float) 149);
  pivot[7] = fft.calcAvg((float) 150, (float) 199);
  pivot[8] = fft.calcAvg((float) 200, (float) 249);
  pivot[9] = fft.calcAvg((float) 250, (float) 299);
  pivot[10] = fft.calcAvg((float) 300, (float) 349);
  
  int cur_freq = 350;
  int freq_width = (max_freq-350)/(bins-8);
  for (int i = 11; i < bins; i++) {
    pivot[i] = fft.calcAvg((float) cur_freq, (float) cur_freq+freq_width);
    cur_freq += freq_width;
  }
  
  // scale array
  for (int i = 0; i < bins; i++) {
    pivot[i] = c*pivot[i];
  }
  
  // create delay for smooth effects then
  // safely convert amplitudes into streamable data
  for(int i = 0; i < bins; i++){
    freq_height[i] = getDelayedHeight(freq_height[i], pivot[i]);
    sig[i+1] = ampToChar(freq_height[i]);
  }
  // protocol to let arduino know how long the message will be
  sig[0] = byte(bins);

  // send data if ready
  if (conn != "disconnected" && arduino.available() > 0) {
    arduino.read();
    arduino.write(sig);
  }
}

byte ampToChar(float h)
{
  if (h >= 255) {
    return byte(255);
  } else if (h <= 0) {
    return byte(0);
  } else {
    return byte(int(h));
  }
}

// this only works consistantly because the processing language trys to draw with 60fps
float getDelayedHeight(float oldh, float newh)
{
  if(newh >= oldh - delay/6.0) {
    return newh;
  } else {
    return oldh - delay/6.0;
  }
}


void sendAmbiance()
{
  // send data if ready
  if (conn != "disconnected" && arduino.available() > 0) {
    arduino.read();
    arduino.write(getSectors(getScreen()));
  }
}

byte[] getSectors(PImage screen) {
  int w = screen.width/bins;
  int h = screen.height;
  byte[] ambColors = new byte[bins*3+1];
  for (int i = 1; i < bins+1; i++) {
    byte[] rgbs = getAvgColor(screen.get((i-1)*w, 0, w, h));
    ambColors[3*i-2] = byte(rgbs[0]);
    ambColors[3*i-1] = byte(rgbs[1]);
    ambColors[3*i]   = byte(rgbs[2]);
  }
  ambColors[0] = byte(ambColors.length-1);
  return ambColors;
}

byte[] getAvgColor(PImage sector) {
  int red = 0;
  int green = 0;
  int blue = 0;
  int size = sector.pixels.length;
  for (int i = 0; i < size; i++){
    red += red(sector.pixels[i]);
    green += green(sector.pixels[i]);
    blue += blue(sector.pixels[i]);
  }
  return new byte[]{ampToChar(red/size), ampToChar(green/size), ampToChar(blue/size)};
}

PImage getScreen() {
  GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
  GraphicsDevice[] gs = ge.getScreenDevices();
  DisplayMode mode = gs[0].getDisplayMode();
  Rectangle bounds = new Rectangle(0, 0, mode.getWidth(), mode.getHeight());
  BufferedImage desktop = new BufferedImage(mode.getWidth(), mode.getHeight(), BufferedImage.TYPE_INT_RGB);

  try {
    desktop = new Robot(gs[0]).createScreenCapture(bounds);
  }
  catch(AWTException e) {
    System.err.println("Screen capture failed.");
  }

  return (new PImage(desktop));
}
 
 
void stop()
{
  // always close Minim audio classes when you finish with them
  if (arduino != null) {
    arduino.stop();
  }
  in.close();
  minim.stop();
 
  super.stop();
}