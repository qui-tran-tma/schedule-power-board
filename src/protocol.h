#pragma once

#include <stddef.h>
#include <stdint.h>

// nanopb request/response handling, transport-agnostic.
namespace protocol {

constexpr size_t kMaxFrame = 128;  // fits in negotiated MTU (185)

// Decode a Request, act on it, encode a Response into out.
// Returns encoded length (0 if encoding failed).
size_t handle(const uint8_t* in, size_t inLen, uint8_t* out, size_t outCap);

// Encode an unsolicited status Response (seq = 0). Returns encoded length (0 on failure).
size_t encodeStatus(uint8_t* out, size_t outCap);

}  // namespace protocol
