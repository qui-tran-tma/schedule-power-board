#pragma once

// Serial (USB CDC) bench console for relays. Non-blocking, call tick() from loop().
//   "1 on" / "1 off" / "1"   set or toggle CH1 (same for 2, 3)
//   "all on" / "all off"     every channel
//   "?"                      print states
// "on" = load powered (coil released, COM-NC closed), "off" = coil energised.
namespace console {

void begin();
void tick();

}  // namespace console
