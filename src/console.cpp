#include "console.h"

#include <Arduino.h>

#include <cctype>
#include <cstring>

#include "pins.h"
#include "relay.h"

namespace console {
namespace {

constexpr size_t kLineMax = 32;
char g_line[kLineMax];
size_t g_len = 0;

void printStatus() {
  for (uint8_t ch = 1; ch <= relay::kChannelCount; ++ch) {
    const bool on = relay::isPowerOn(ch);
    Serial.printf("CH%u (GPIO%u): %s\n", ch, pins::kRelays[ch - 1],
                  on ? "ON  (coil released, load powered)" : "OFF (coil energised, load cut)");
  }
}

void printHelp() {
  Serial.println("relay console: '<ch> on|off', '<ch>' toggle, 'all on|off', '?' status");
}

void apply(uint8_t ch, int action) {  // action: 1 on, 0 off, -1 toggle
  const bool next = action < 0 ? !relay::isPowerOn(ch) : action == 1;
  relay::setPower(ch, next);
  Serial.printf("CH%u (GPIO%u) -> %s\n", ch, pins::kRelays[ch - 1], next ? "ON" : "OFF");
}

void handle(char* line) {
  for (char* p = line; *p; ++p) *p = static_cast<char>(tolower(*p));
  char* target = strtok(line, " \t");
  if (target == nullptr) return;
  char* verb = strtok(nullptr, " \t");

  int action = -1;
  if (verb != nullptr) {
    if (strcmp(verb, "on") == 0 || strcmp(verb, "1") == 0) {
      action = 1;
    } else if (strcmp(verb, "off") == 0 || strcmp(verb, "0") == 0) {
      action = 0;
    } else {
      printHelp();
      return;
    }
  }

  if (strcmp(target, "?") == 0 || strcmp(target, "s") == 0) {
    printStatus();
  } else if (strcmp(target, "all") == 0) {
    if (action < 0) {
      printHelp();
      return;
    }
    for (uint8_t ch = 1; ch <= relay::kChannelCount; ++ch) apply(ch, action);
  } else if (strlen(target) == 1 && target[0] >= '1' && target[0] <= '0' + relay::kChannelCount) {
    apply(static_cast<uint8_t>(target[0] - '0'), action);
  } else {
    printHelp();
  }
}

}  // namespace

void begin() {
  if (relay::kChannelCount == 0) return;
  printHelp();
  printStatus();
}

void tick() {
  if (relay::kChannelCount == 0) return;
  while (Serial.available() > 0) {
    const int c = Serial.read();
    if (c == '\r' || c == '\n') {
      if (g_len > 0) {
        g_line[g_len] = '\0';
        handle(g_line);
        g_len = 0;
      }
    } else if (g_len < kLineMax - 1) {
      g_line[g_len++] = static_cast<char>(c);
    }
  }
}

}  // namespace console
