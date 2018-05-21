/**
 *  @file       floppy-music.ino
 *  @author     Daniel Fernau
 *  @date       05/21/2018
 */

#include <TimerOne.h>

int drivePosition[] = {0, 0, 0, 0, 0, 0, 0, 0}; // initialize drive position array for 8 drives, min 0, max 158
int driveDirection[] = {LOW, LOW, LOW, LOW, LOW, LOW, LOW, LOW}; // initialize drive movement direction array for 8 drives, LOW -> move to next track on next step, HIGH -> move to previous track on next step

bool drivePlayTone[] = {false, false, false, false, false, false, false, false}; // array containing which drives should play a tone and which not
int driveFrequency[] = {0, 0, 0, 0, 0, 0, 0, 0}; // store which frequency to play for each drive
int driveCycle[] = {0, 0, 0, 0, 0, 0, 0, 0}; // store current drive cycles

int driveDirectionPin[] = {2, 4, 6, 8, 10, 12, 14, 16}; // array of drive direction control pins
int driveStepPin[] = {3, 5, 7, 9, 11, 13, 15, 17}; // array of drive step control pins

void setup() {
  // put your setup code here, to run once:
  Timer1.initialize(100); // init timer

  pinMode(driveDirectionPin[0], OUTPUT); // 1st drive, direction control
  pinMode(driveStepPin[0], OUTPUT); // 1st drive, step control

  pinMode(driveDirectionPin[1], OUTPUT); // 2nd drive, direction control
  pinMode(driveStepPin[1], OUTPUT); // 2nd drive, step control

  pinMode(driveDirectionPin[2], OUTPUT); // 3rd drive, direction control
  pinMode(driveStepPin[2], OUTPUT); // 3rd drive, step control

  pinMode(driveDirectionPin[3], OUTPUT); // 4th drive, direction control
  pinMode(driveStepPin[3], OUTPUT); // 4th drive, step control

  pinMode(driveDirectionPin[4], OUTPUT); // 5th drive, direction control
  pinMode(driveStepPin[4], OUTPUT); // 5th drive, step control

  pinMode(driveDirectionPin[5], OUTPUT); // 6th drive, direction control
  pinMode(driveStepPin[5], OUTPUT); // 6th drive, step control

  pinMode(driveDirectionPin[6], OUTPUT); // 7th drive, direction control
  pinMode(driveStepPin[6], OUTPUT); // 7th drive, step control

  pinMode(driveDirectionPin[7], OUTPUT); // 8th drive, direction control
  pinMode(driveStepPin[7], OUTPUT); // 8th drive, step control

  Serial.begin(9600);
  resetDrives();

  delay(3000);

  Timer1.attachInterrupt(interruptFunction);
}

int combineTwoIntegers(int a, int b) {
  String one = String(a);
  String two = String(b);
  String oneAndTwo = one + two;
  int combinedIntegers = oneAndTwo.toInt();
  return combinedIntegers;
}

void loop() {
  // put your main code here, to run repeatedly:
  int incomingByte;
  if (Serial.available() > 0) {
    // read the incoming byte:
    char buffer[] = {0, 0, 0, 0};
    Serial.readBytes(buffer, 4);

    int driveId = buffer[0];
    int midiNoteCycles1 = buffer[1];
    int midiNoteCycles2 = buffer[2];
    int midiNote = combineTwoIntegers(midiNoteCycles1, midiNoteCycles2);
    int stopNote = buffer[3];

    if (stopNote == 1) {
      Serial.println(); // blink tx led
      if (driveId == 1) {
        drivePlayTone[0] = false;
      }
      if (driveId == 2) {
        drivePlayTone[1] = false;
      }
      if (driveId == 3) {
        drivePlayTone[2] = false;
      }
      if (driveId == 4) {
        drivePlayTone[3] = false;
      }
      if (driveId == 5) {
        drivePlayTone[4] = false;
      }
      if (driveId == 6) {
        drivePlayTone[5] = false;
      }
      if (driveId == 7) {
        drivePlayTone[6] = false;
      }
      if (driveId == 8) {
        drivePlayTone[7] = false;
      }
    }

    if (stopNote == 0) {
      if (driveId == 1) {
        if (midiNote != 0) {
          drivePlayTone[0] = true;
          driveFrequency[0] = midiNote;
        }
      }
      if (driveId == 2) {
        if (midiNote != 0) {
          drivePlayTone[1] = true;
          driveFrequency[1] = midiNote;
        }
      }
      if (driveId == 3) {
        if (midiNote != 0) {
          drivePlayTone[2] = true;
          driveFrequency[2] = midiNote;
        }
      }
      if (driveId == 4) {
        if (midiNote != 0) {
          drivePlayTone[3] = true;
          driveFrequency[3] = midiNote;
        }
      }
      if (driveId == 5) {
        if (midiNote != 0) {
          drivePlayTone[4] = true;
          driveFrequency[4] = midiNote;
        }
      }
      if (driveId == 6) {
        if (midiNote != 0) {
          drivePlayTone[5] = true;
          driveFrequency[5] = midiNote;
        }
      }
      if (driveId == 7) {
        if (midiNote != 0) {
          drivePlayTone[6] = true;
          driveFrequency[6] = midiNote;
        }
      }
      if (driveId == 8) {
        if (midiNote != 0) {
          drivePlayTone[7] = true;
          driveFrequency[7] = midiNote;
        }
      }
    }
  }
}

void moveOneStep(bool driveResetMode, int drive, int directionPin, int stepPin) {
  if (driveResetMode) {
    digitalWrite(directionPin, HIGH);
    driveDirection[drive] = HIGH;
  } else if (drivePosition[drive] <= 77) {
    digitalWrite(directionPin, LOW);
    driveDirection[drive] = LOW;
  } else if (drivePosition[drive] < 154) {
    digitalWrite(directionPin, HIGH);
    driveDirection[drive] = HIGH;
  } else if (drivePosition[drive] == 154) {
    digitalWrite(directionPin, HIGH);
    driveDirection[drive] = HIGH;
    drivePosition[drive] = 0;
  }

  digitalWrite(stepPin, LOW);
  digitalWrite(stepPin, HIGH);
  drivePosition[drive]++;
}

void resetDrives() {
  for (int i = 0; i < 80; i++) {
    for (int j = 0; j < 8; j++) {
      moveOneStep(true, j, driveDirectionPin[j], driveStepPin[j]);
    }
    delay(3);
  };

  memset(drivePosition, 0, sizeof drivePosition); // reset all saved drive positions to 0
}

void interruptFunction() {
  if (drivePlayTone[0]) {
    if (driveCycle[0] >= driveFrequency[0]) {
      moveOneStep(false, 0, driveDirectionPin[0], driveStepPin[0]);
      driveCycle[0] = 1;
    } else {
      driveCycle[0]++;
    }
  }
  if (drivePlayTone[1]) {
    if (driveCycle[1] >= driveFrequency[1]) {
      moveOneStep(false, 1, driveDirectionPin[1], driveStepPin[1]);
      driveCycle[1] = 1;
    } else {
      driveCycle[1]++;
    }
  }
  if (drivePlayTone[2]) {
    if (driveCycle[2] >= driveFrequency[2]) {
      moveOneStep(false, 2, driveDirectionPin[2], driveStepPin[2]);
      driveCycle[2] = 1;
    } else {
      driveCycle[2]++;
    }
  }
  if (drivePlayTone[3]) {
    if (driveCycle[3] >= driveFrequency[3]) {
      moveOneStep(false, 3, driveDirectionPin[3], driveStepPin[3]);
      driveCycle[3] = 1;
    } else {
      driveCycle[3]++;
    }
  }
  if (drivePlayTone[4]) {
    if (driveCycle[4] >= driveFrequency[4]) {
      moveOneStep(false, 4, driveDirectionPin[4], driveStepPin[4]);
      driveCycle[4] = 1;
    } else {
      driveCycle[4]++;
    }
  }
  if (drivePlayTone[5]) {
    if (driveCycle[5] >= driveFrequency[5]) {
      moveOneStep(false, 5, driveDirectionPin[5], driveStepPin[5]);
      driveCycle[5] = 1;
    } else {
      driveCycle[5]++;
    }
  }
  if (drivePlayTone[6]) {
    if (driveCycle[6] >= driveFrequency[6]) {
      moveOneStep(false, 6, driveDirectionPin[6], driveStepPin[6]);
      driveCycle[6] = 1;
    } else {
      driveCycle[6]++;
    }
  }
  if (drivePlayTone[7]) {
    if (driveCycle[7] >= driveFrequency[7]) {
      moveOneStep(false, 7, driveDirectionPin[7], driveStepPin[7]);
      driveCycle[7] = 1;
    } else {
      driveCycle[7]++;
    }
  }
}


