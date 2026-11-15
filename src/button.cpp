#include "button.h"

#include <Arduino.h>
#include <driver/gpio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <math.h>

#include <array>

#include "pins.h"

#ifndef PINION_RADIUS_MM
// 20 T pinion, module 1.273 (docs/cad/button_pusher.py): pitch radius = 40 mm / pi,
// so 180 deg moves the rack 40 mm, 0.222 mm per degree.
#define PINION_RADIUS_MM 12.73f
#endif
#ifndef STROKE_MM
#define STROKE_MM 40.0f  // usable rack travel
#endif
#ifndef BUTTON_HOME_MM
#define BUTTON_HOME_MM 0.0f  // released position (0 = fully pulled in)
#endif
#ifndef BUTTON_DEPTH_MM
#define BUTTON_DEPTH_MM 10.0f  // how far a press pushes out from home
#endif
#ifndef SPEED_MM_PER_S
#define SPEED_MM_PER_S 80.0f  // slew rate; 10 mm takes 125 ms
#endif

namespace button {
namespace {

constexpr size_t kCount = pins::kButtonServos.size();

constexpr uint32_t kFreqHz = 50;         // 20 ms servo frame
constexpr uint8_t kResolutionBits = 14;  // ESP32-C3 LEDC max
constexpr float kPeriodUs = 1000000.0f / kFreqHz;
constexpr float kMinPulseUs = 500.0f;  // SG90 typical range
constexpr float kMaxPulseUs = 2400.0f;
constexpr float kMaxAngleDeg = 180.0f;
constexpr float kMmPerDeg = PINION_RADIUS_MM * static_cast<float>(M_PI) / 180.0f;
constexpr float kReachMm = kMmPerDeg * kMaxAngleDeg;
constexpr float kStrokeMm = STROKE_MM < kReachMm ? STROKE_MM : kReachMm;
constexpr float kHomeMm = BUTTON_HOME_MM;
constexpr float kDownMm =
    BUTTON_HOME_MM + BUTTON_DEPTH_MM < kStrokeMm ? BUTTON_HOME_MM + BUTTON_DEPTH_MM : kStrokeMm;
constexpr uint32_t kSlewTickMs = 20;
constexpr float kSlewStepMm = SPEED_MM_PER_S * kSlewTickMs / 1000.0f;
// One-way travel time; added to hold/gap so they measure contact/release time, not travel.
constexpr uint32_t kTravelMs =
    static_cast<uint32_t>((kDownMm - kHomeMm) / SPEED_MM_PER_S * 1000.0f + 0.5f);

static_assert(kCount <= 4, "Status.buttons max_count is 4 in power_board.options");
static_assert(kCount <= 6, "ESP32-C3 has 6 LEDC channels");

enum class Phase : uint8_t { kIdle, kDown, kUp };

struct Pusher {
  float currentMm = kHomeMm;
  float targetMm = kHomeMm;
  Phase phase = Phase::kIdle;
  uint32_t phaseStartMs = 0;
  uint32_t pressesLeft = 0;
  uint32_t holdMs = 0;
  uint32_t gapMs = 0;
};

std::array<Pusher, kCount> g_pushers{};
uint32_t g_lastSlewMs = 0;

// press()/stop() run on the NimBLE host task, tick() on the loop task.
SemaphoreHandle_t g_lock = nullptr;

struct Guard {
  Guard() { xSemaphoreTake(g_lock, portMAX_DELAY); }
  ~Guard() { xSemaphoreGive(g_lock); }
  Guard(const Guard&) = delete;
  Guard& operator=(const Guard&) = delete;
};

bool valid(uint32_t id) { return id >= 1 && id <= kCount; }

void writeMm(size_t i, float mm) {
  const float angle = mm / kMmPerDeg;
  const float pulseUs = kMinPulseUs + (kMaxPulseUs - kMinPulseUs) * angle / kMaxAngleDeg;
  const uint32_t duty =
      static_cast<uint32_t>(pulseUs * ((1UL << kResolutionBits) - 1) / kPeriodUs);
  ledcWrite(i, duty);  // LEDC channel = pusher index
}

void slew(size_t i) {
  Pusher& p = g_pushers[i];
  const float diff = p.targetMm - p.currentMm;
  if (diff == 0.0f) return;
  p.currentMm = fabsf(diff) <= kSlewStepMm ? p.targetMm
                                           : p.currentMm + (diff > 0 ? kSlewStepMm : -kSlewStepMm);
  writeMm(i, p.currentMm);
}

void startPhase(Pusher& p, Phase phase, uint32_t now) {
  p.phase = phase;
  p.phaseStartMs = now;
  p.targetMm = phase == Phase::kDown ? kDownMm : kHomeMm;
}

// Advance one pusher's sequence. Returns true when the sequence completed.
bool step(size_t i, uint32_t now) {
  Pusher& p = g_pushers[i];
  if (p.phase == Phase::kIdle) return false;
  const uint32_t elapsed = now - p.phaseStartMs;

  if (p.phase == Phase::kDown) {
    if (elapsed < kTravelMs + p.holdMs) return false;
    --p.pressesLeft;
    startPhase(p, Phase::kUp, p.phaseStartMs + kTravelMs + p.holdMs);  // no drift
    return false;
  }

  // kUp: last press only needs travel time to get home; between presses wait the gap.
  const uint32_t upMs = p.pressesLeft == 0 ? kTravelMs : kTravelMs + p.gapMs;
  if (elapsed < upMs) return false;
  if (p.pressesLeft == 0) {
    p.phase = Phase::kIdle;
    log_i("button %u done", static_cast<unsigned>(i + 1));
    return true;
  }
  startPhase(p, Phase::kDown, p.phaseStartMs + upMs);
  return false;
}

}  // namespace

void begin() {
  g_lock = xSemaphoreCreateMutex();
  for (size_t i = 0; i < kCount; ++i) {
    gpio_hold_dis(static_cast<gpio_num_t>(pins::kButtonServos[i]));
    ledcSetup(i, kFreqHz, kResolutionBits);
    ledcAttachPin(pins::kButtonServos[i], i);
    writeMm(i, kHomeMm);
  }
  log_i("%u button pusher(s), travel %u ms", static_cast<unsigned>(kCount),
        static_cast<unsigned>(kTravelMs));
}

size_t count() { return kCount; }

void prepareSleep() {
  for (size_t i = 0; i < kCount; ++i) {
    const uint8_t pin = pins::kButtonServos[i];
    ledcDetachPin(pin);
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
    gpio_hold_en(static_cast<gpio_num_t>(pin));
  }
}

Result validate(uint32_t buttonId, uint32_t pressCount, uint32_t holdMs, uint32_t gapMs) {
  if (!valid(buttonId)) return Result::kBadButton;
  if (pressCount == 0) pressCount = 1;
  if (gapMs == 0) gapMs = kDefaultGapMs;
  if (pressCount > kMaxPressCount || holdMs < kMinHoldMs || holdMs > kMaxHoldMs ||
      gapMs < kMinGapMs || gapMs > kMaxGapMs) {
    return Result::kBadArgs;
  }
  return Result::kOk;
}

Result press(uint32_t buttonId, uint32_t pressCount, uint32_t holdMs, uint32_t gapMs) {
  const Result check = validate(buttonId, pressCount, holdMs, gapMs);
  if (check != Result::kOk) return check;
  if (pressCount == 0) pressCount = 1;
  if (gapMs == 0) gapMs = kDefaultGapMs;
  Guard guard;
  Pusher& p = g_pushers[buttonId - 1];
  if (p.phase != Phase::kIdle) return Result::kBusy;

  p.pressesLeft = pressCount;
  p.holdMs = holdMs;
  p.gapMs = gapMs;
  startPhase(p, Phase::kDown, millis());
  log_i("button %u press x%u hold %u ms gap %u ms", static_cast<unsigned>(buttonId),
        static_cast<unsigned>(pressCount), static_cast<unsigned>(holdMs),
        static_cast<unsigned>(gapMs));
  return Result::kOk;
}

Result stop(uint32_t buttonId) {
  if (!valid(buttonId)) return Result::kBadButton;
  Guard guard;
  Pusher& p = g_pushers[buttonId - 1];
  if (p.phase != Phase::kIdle) log_i("button %u stopped", static_cast<unsigned>(buttonId));
  p.phase = Phase::kIdle;
  p.pressesLeft = 0;
  p.targetMm = kHomeMm;
  return Result::kOk;
}

bool isPressing(uint32_t buttonId) {
  if (!valid(buttonId)) return false;
  Guard guard;
  return g_pushers[buttonId - 1].phase != Phase::kIdle;
}

bool tick() {
  Guard guard;
  const uint32_t now = millis();
  bool finished = false;
  for (size_t i = 0; i < kCount; ++i) finished |= step(i, now);
  if (now - g_lastSlewMs >= kSlewTickMs) {
    g_lastSlewMs = now;
    for (size_t i = 0; i < kCount; ++i) slew(i);
  }
  return finished;
}

}  // namespace button
