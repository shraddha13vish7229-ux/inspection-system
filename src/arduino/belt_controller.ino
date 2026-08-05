/*
 * AUTOMATED QUALITY INSPECTION SYSTEM
 * Belt & Actuator Controller: Arduino Uno R3
 * Revision: 1.0.0
 * 
 * Features:
 * - Stepper motor belt drive with constant speed
 * - Photogate trigger detection
 * - Solenoid actuator control for defective item rejection
 * - Emergency stop with hardware interrupt
 * - Serial communication with Jetson Nano
 */

// ==================== PIN DEFINITIONS ====================
#define STEP_PIN      2
#define DIR_PIN       3
#define ENABLE_PIN    4
#define SOLENOID_PIN  5
#define PHOTOGATE_PIN 6
#define KILL_PIN      7
#define LED_RUN       8
#define LED_FAULT     9

// ==================== CONSTANTS ====================
#define BELT_PPS      400       // Steps per second
#define SOLENOID_MS   60        // Solenoid activation duration
#define REJECT_DELAY  850       // ms from photogate to diverter

// ==================== GLOBALS ====================
volatile bool article_present = false;
volatile unsigned long gate_timestamp = 0;
bool belt_running = false;
String pending_command = "";
unsigned long reject_timer = 0;
bool reject_pending = false;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);

  // Pin modes
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(SOLENOID_PIN, OUTPUT);
  pinMode(PHOTOGATE_PIN, INPUT_PULLUP);
  pinMode(KILL_PIN, INPUT_PULLUP);
  pinMode(LED_RUN, OUTPUT);
  pinMode(LED_FAULT, OUTPUT);

  // Initial states
  digitalWrite(DIR_PIN, HIGH);   // Forward direction
  digitalWrite(ENABLE_PIN, LOW); // Enable driver
  digitalWrite(SOLENOID_PIN, LOW);
  digitalWrite(LED_RUN, HIGH);
  digitalWrite(LED_FAULT, LOW);

  // Interrupts
  attachInterrupt(digitalPinToInterrupt(PHOTOGATE_PIN), photogateISR, FALLING);
  attachInterrupt(digitalPinToInterrupt(KILL_PIN), killISR, FALLING);

  belt_running = true;
  Serial.println("CONTROLLER_READY");
}

// ==================== MAIN LOOP ====================
void loop() {
  // Stepper pulse generation (non-blocking)
  if (belt_running) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(1250);  // 400 PPS
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(1250);
  }

  // Photogate event handling
  if (article_present) {
    article_present = false;
    Serial.print("GATE:");
    Serial.println(gate_timestamp);
  }

  // Serial command handling
  if (Serial.available()) {
    pending_command = Serial.readStringUntil('\n');
    pending_command.trim();

    if (pending_command.startsWith("REJECT:")) {
      reject_pending = true;
      reject_timer = millis() + REJECT_DELAY;
    }
    else if (pending_command == "ACCEPT") {
      Serial.println("LOG:ACCEPT");
    }
    else if (pending_command == "START") {
      belt_running = true;
      digitalWrite(ENABLE_PIN, LOW);
      digitalWrite(LED_RUN, HIGH);
      Serial.println("ACK:START");
    }
    else if (pending_command == "STOP") {
      belt_running = false;
      digitalWrite(ENABLE_PIN, HIGH);
      digitalWrite(LED_RUN, LOW);
      Serial.println("ACK:STOP");
    }
  }

  // Scheduled rejection
  if (reject_pending && millis() >= reject_timer) {
    fireSolenoid();
    Serial.println("LOG:" + pending_command);
    reject_pending = false;
  }
}

// ==================== ACTUATION ====================
void fireSolenoid() {
  digitalWrite(SOLENOID_PIN, HIGH);
  delay(SOLENOID_MS);
  digitalWrite(SOLENOID_PIN, LOW);
}

// ==================== INTERRUPTS ====================
void photogateISR() {
  article_present = true;
  gate_timestamp = millis();
}

void killISR() {
  belt_running = false;
  digitalWrite(ENABLE_PIN, HIGH);
  digitalWrite(SOLENOID_PIN, LOW);
  digitalWrite(LED_RUN, LOW);
  digitalWrite(LED_FAULT, HIGH);
  Serial.println("EMERGENCY_STOP");
}
