/*
 * Microstepping demo
 *
 * This requires that M0, M1 be connected in addition to STEP,DIR
 *
 * Copyright (C)2015 Laurentiu Badea
 *
 * This file may be redistributed under the terms of the MIT license.
 * A copy of this license has been included with this distribution in the file LICENSE.
 */

#include <Arduino.h>
#include "DRV8834.h"
#include "A4988.h"
#include "DRV8825.h"

// Motor steps per revolution. Most steppers are 200 steps or 1.8 degrees/step
#define MOTOR_STEPS 200

// Number of Motor rotations to complete one Filter Wheel section
#define MOTOR_ROTATIONS 275

//Define the Number of Filters on your Filter Wheel
#define NRFILTERS 5

//Define the Start Position of the Filter Wheel when the system is started.
#define STARTPOSITION 0

// This sets the Current Filter Wheel Position. Always starts in position 0.
int CurrentPosition = STARTPOSITION;

// All the wires needed for full functionality
#define DIR 4
#define STEP 5
#define ENBL 6

// 2-wire basic config, microstepping is hardwired on the driver
// BasicStepperDriver stepper(DIR, STEP);

/* Microstep control for DRV8825
    MODE0 MODE1 MODE2 Microstep Resolution
    Low   Low   Low   Full step   = 1
    High  Low   Low   Half step   = 2
    Low   High  Low   1/4 step    = 4
    High  High  Low   1/8 step    = 8
    Low   Low   High  1/16 step   = 16
    High  Low   High  1/32 step
    Low   High  High  1/32 step
    High  High  High  1/32 step   = 32
 */

#define MODE0 11
#define MODE1 12
#define MODE2 13

DRV8825 stepper(MOTOR_STEPS, DIR, STEP, ENBL, MODE0, MODE1, MODE2);

void setup() {
    /*
     * Set target motor RPM.
     * These motors can do up to about 200rpm.
     * Too high will result in a high pitched whine and the motor does not move.
     */

    Serial.flush();
    Serial.begin(9600);  // Baud rate, make sure this is the same as ASCOM driver
    stepper.disable();
    Serial.write("Setup complete!#");
}

void loop() {

  String ASCOMcmd;
  if (Serial.available() >0) {
    ASCOMcmd = Serial.readStringUntil('#');  // Terminator so arduino knows when the message ends
    if (ASCOMcmd=="GETFILTER") {
      Serial.print(CurrentPosition);
      Serial.println("#");  // Similarly, so ASCOM knows
    }

  // Get the int value of the Filter Postition. cmd is FILTER0 - FILTERx. Last position in cmd is the number of the required Filter.
  //   So lets get that number
  //int NextPosition = (ASCOMcmd.substring(ASCOMcmd.length()-1)).toInt();
  else if (ASCOMcmd == "FILTER0") MoveFilter(0);
  else if (ASCOMcmd == "FILTER1") MoveFilter(1);
  else if (ASCOMcmd == "FILTER2") MoveFilter(2);
  else if (ASCOMcmd == "FILTER3") MoveFilter(3);
  else if (ASCOMcmd == "FILTER4") MoveFilter(4);

  }
}

// We would like to get to the new filter position as quickly as possible. This means moving the filter wheel either clockwise or counter clockwise.
// This function will determine the shortest path and return either positive rotation or negative rotation.
int getShortestPath(int NextPosition){

    int ClockWiseSteps = 0;
    int CounterClockWiseSteps = 0;

    if (NextPosition < CurrentPosition) {NextPosition == NextPosition + NRFILTERS;}

    ClockWiseSteps = NextPosition - CurrentPosition;
    CounterClockWiseSteps = ClockWiseSteps - NRFILTERS;

    if ((-CounterClockWiseSteps) < ClockWiseSteps) {return CounterClockWiseSteps;}
    else {return ClockWiseSteps;}
}

void MoveFilter(int NextPosition) {

  int RotateSteps = getShortestPath(NextPosition);
  int Move = RotateSteps * MOTOR_ROTATIONS;

  stepper.enable();

  stepper.setRPM(120);
  stepper.setMicrostep(1);

  stepper.move(Move);

  CurrentPosition = NextPosition;    // Note that the position is always 0 when powered on so have filters oriented properly
  stepper.disable();

  Serial.print(CurrentPosition);
  Serial.println("#");  // Similarly, so ASCOM knows

}