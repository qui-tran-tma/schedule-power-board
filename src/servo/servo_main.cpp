// SG90 servo as a straight push/pull handle (rack and pinion) on ESP32-C3 Super Mini.
// Built only by the c3_servo envs; the C3 power-board envs exclude src/servo/.
//
// Wiring: servo brown/black -> GND, red -> 5V (VBUS), orange/yellow -> SERVO_PIN.
// Power the servo from 5V, not 3V3; share GND with the board.
//
// Mechanics: a pinion on the servo horn drives a straight rack (the handle).
//   travel_mm = PINION_RADIUS_MM * angle_rad
// SG90 turns 180 deg, so max stroke = PINION_RADIUS_MM * pi.
// Position 0 = fully pulled in (servo 0 deg). Handle boots to HOME_MM.
// "Down" = push out (+), "up" = pull back in (-).
//
// Serial commands (115200, newline terminated), distances in cm:
//   1          single click: down GESTURE_DEPTH, up, total 1 s
//   2          double click: down, up, down, up, total 2 s
//   3          press and hold: down, hold 6 s, up
//   s          stop a running gesture and return to where it started
//   go 2.4     go to 2.4 cm extension (absolute)
//   +0.2       push out 0.2 cm        push 0.2   same
//   -0.5       pull in 0.5 cm         pull 0.5   same
//   ?          print position
// Build with -DSERVO_SWEEP to run the handle 0..stroke..0 continuously.

#include <Arduino.h>
#include <math.h>

#ifndef SERVO_PIN
#define SERVO_PIN 0
#endif
#ifndef PINION_RADIUS_MM
// 20 T pinion, module 1.273 (docs/cad/button_pusher.py): pitch radius = 40 mm / pi,
// so 180 deg moves the rack 40 mm, 0.222 mm per degree.
#define PINION_RADIUS_MM 12.73f
#endif
#ifndef STROKE_MM
#define STROKE_MM 40.0f  // usable rack travel; clamped to what 180 deg can reach
#endif
#ifndef HOME_MM
#define HOME_MM 0.0f
#endif
#ifndef SPEED_MM_PER_S
#define SPEED_MM_PER_S 80.0f  // slew rate; 1 cm takes 125 ms, well inside SG90 max speed
#endif
#ifndef GESTURE_DEPTH_MM
#define GESTURE_DEPTH_MM 10.0f  // how far a click pushes down
#endif

namespace {

constexpr uint8_t kLedcChannel = 0;
constexpr uint32_t kFreqHz = 50;         // 20 ms frame
constexpr uint8_t kResolutionBits = 14;  // ESP32-C3 LEDC max is 14 bits (~1.2 us/step at 50 Hz)
constexpr float kPeriodUs = 1000000.0f / kFreqHz;
constexpr uint32_t kTickMs = 20;

// SG90 typical pulse range. Tighten if the servo buzzes at the end stops.
constexpr float kMinPulseUs = 500.0f;
constexpr float kMaxPulseUs = 2400.0f;

constexpr float kMaxAngleDeg = 180.0f;
constexpr float kMmPerDeg = PINION_RADIUS_MM * static_cast<float>(M_PI) / 180.0f;
constexpr float kReachMm = kMmPerDeg * kMaxAngleDeg;
constexpr float kStrokeMm = STROKE_MM < kReachMm ? STROKE_MM : kReachMm;

uint32_t ledcFreq = 0;
float currentMm = HOME_MM;
float targetMm = HOME_MM;

// ---- Gestures --------------------------------------------------------------
// Each step moves to (base + offset) and stays there until durationMs has passed
// since the step began, travel time included. Step durations add up to the gesture time.
struct Step {
  float offsetMm;
  uint32_t durationMs;
};

constexpr float kD = GESTURE_DEPTH_MM;
constexpr Step kSingle[] = {{kD, 500}, {0, 500}};                              // 1 s
constexpr Step kDouble[] = {{kD, 500}, {0, 500}, {kD, 500}, {0, 500}};         // 2 s
constexpr Step kHold[] = {{kD, 6000 + 125}, {0, 500}};  // 125 ms travel, then 6 s held down

struct Gesture {
  const char* name;
  const Step* steps;
  size_t count;
};

constexpr Gesture kGestures[] = {
    {"single click", kSingle, sizeof(kSingle) / sizeof(Step)},
    {"double click", kDouble, sizeof(kDouble) / sizeof(Step)},
    {"press and hold", kHold, sizeof(kHold) / sizeof(Step)},
};

const Gesture* active = nullptr;
size_t stepIndex = 0;
uint32_t stepStartMs = 0;
float baseMm = 0;

void writeMm(float mm) {
  const float angle = mm / kMmPerDeg;
  const float pulseUs = kMinPulseUs + (kMaxPulseUs - kMinPulseUs) * angle / kMaxAngleDeg;
  const uint32_t duty = static_cast<uint32_t>(pulseUs * ((1UL << kResolutionBits) - 1) / kPeriodUs);
  ledcWrite(kLedcChannel, duty);
}

void setTarget(float mm, bool log = true) {
  const float clamped = constrain(mm, 0.0f, kStrokeMm);
  if (clamped != mm) Serial.printf("[handle] %.1f cm out of range, clamped\n", mm / 10.0f);
  targetMm = clamped;
  if (log) Serial.printf("[handle] -> %.2f cm (%.1f deg)\n", targetMm / 10.0f, targetMm / kMmPerDeg);
}

// Step currentMm toward targetMm at SPEED_MM_PER_S. Call every kTickMs.
void slew() {
  constexpr float kStepMm = SPEED_MM_PER_S * kTickMs / 1000.0f;
  const float diff = targetMm - currentMm;
  if (diff == 0.0f) return;
  currentMm = fabsf(diff) <= kStepMm ? targetMm : currentMm + (diff > 0 ? kStepMm : -kStepMm);
  writeMm(currentMm);
}

void startGesture(const Gesture& g) {
  baseMm = targetMm;
  if (baseMm + kD > kStrokeMm) {
    baseMm = kStrokeMm - kD;  // not enough room below: start the click from higher up
    Serial.printf("[handle] base moved up to %.2f cm to fit a %.1f cm click\n", baseMm / 10.0f,
                  kD / 10.0f);
  }
  active = &g;
  stepIndex = 0;
  stepStartMs = millis();
  setTarget(baseMm + g.steps[0].offsetMm, false);
  Serial.printf("[handle] %s from %.2f cm\n", g.name, baseMm / 10.0f);
}

void stopGesture(const char* why) {
  if (!active) return;
  Serial.printf("[handle] %s %s, back at %.2f cm\n", active->name, why, baseMm / 10.0f);
  setTarget(baseMm, false);
  active = nullptr;
}

void runGesture() {
  if (!active) return;
  const uint32_t now = millis();
  if (now - stepStartMs < active->steps[stepIndex].durationMs) return;
  stepStartMs += active->steps[stepIndex].durationMs;  // no drift between steps
  if (++stepIndex >= active->count) {
    stopGesture("done");
    return;
  }
  setTarget(baseMm + active->steps[stepIndex].offsetMm, false);
}

constexpr const char* kHelp =
    "[handle] commands: 1 single | 2 double | 3 hold | s stop | go <cm> | +<cm> | -<cm> | "
    "push <cm> | pull <cm> | ?";

void handleCommand(String line) {
  line.trim();
  line.toLowerCase();
  if (line.isEmpty()) return;
  if (line == "?") {
    Serial.printf("[handle] at %.2f cm, target %.2f cm, stroke %.1f cm%s\n", currentMm / 10.0f,
                  targetMm / 10.0f, kStrokeMm / 10.0f, active ? ", gesture running" : "");
    return;
  }
  if (line == "s") {
    stopGesture("stopped");
    return;
  }
  if (active) {
    Serial.printf("[handle] busy with %s, send s to stop\n", active->name);
    return;
  }
  if (line == "1" || line == "2" || line == "3") {
    startGesture(kGestures[line[0] - '1']);
  } else if (line.startsWith("go")) {
    setTarget(line.substring(2).toFloat() * 10.0f);
  } else if (line.startsWith("push")) {
    setTarget(targetMm + line.substring(4).toFloat() * 10.0f);
  } else if (line.startsWith("pull")) {
    setTarget(targetMm - line.substring(4).toFloat() * 10.0f);
  } else if (line[0] == '+' || line[0] == '-') {
    setTarget(targetMm + line.toFloat() * 10.0f);
  } else {
    Serial.println(kHelp);
  }
}

void printBanner() {
  Serial.printf("c3_servo ready, GPIO%d, %.3f mm/deg, stroke %.1f cm, at %.2f cm\n", SERVO_PIN,
                kMmPerDeg, kStrokeMm / 10.0f, currentMm / 10.0f);
  if (ledcFreq == 0) Serial.println("[handle] ERROR: LEDC PWM setup failed, no servo signal");
  else Serial.printf("[handle] PWM %u Hz, %u-bit\n", ledcFreq, kResolutionBits);
  Serial.println(kHelp);
}

// Native USB CDC: anything printed before the monitor attaches is lost (the port
// re-enumerates on reset). Re-print the banner whenever a host connects.
void pollHostConnect() {
  static bool wasConnected = false;
  const bool connected = static_cast<bool>(Serial);
  if (connected && !wasConnected) {
    delay(100);
    printBanner();
  }
  wasConnected = connected;
}

// Non-blocking line reader. Echoes input since the monitor does not.
void pollSerial() {
  static String buf;
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\r' || c == '\n') {
      if (buf.length() > 0) {
        Serial.println();
        handleCommand(buf);
        buf = "";
      }
    } else if (buf.length() < 32) {
      buf += c;
      Serial.print(c);
    }
  }
}

}  // namespace

void setup() {
  ledcFreq = ledcSetup(kLedcChannel, kFreqHz, kResolutionBits);
  ledcAttachPin(SERVO_PIN, kLedcChannel);
  writeMm(currentMm);
  Serial.begin(115200);
}

void loop() {
#if defined(SERVO_SWEEP)
  if (currentMm == targetMm) setTarget(targetMm < kStrokeMm / 2 ? kStrokeMm : 0.0f);
#else
  pollSerial();
  runGesture();
#endif
  pollHostConnect();
  slew();
  static uint32_t lastBeat = 0;
  if (millis() - lastBeat >= 10000) {  // heartbeat so a silent monitor still shows life
    lastBeat = millis();
    Serial.printf("[handle] alive, at %.2f cm\n", currentMm / 10.0f);
  }
  delay(kTickMs);
}
