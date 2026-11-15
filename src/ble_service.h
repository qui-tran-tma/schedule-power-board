#pragma once

// BLE GATT transport. One protobuf message per GATT write / notification.
//   Service : 6e400001-b5a3-f393-e0a9-e50e24dcca9e
//   RX      : 6e400002-...  write / write-no-response  (mobile -> board, Request)
//   TX      : 6e400003-...  notify                     (board -> mobile, Response)
namespace ble_service {

void begin();
bool isConnected();

// Battery mode: drop a connection idle for config::kIdleDisconnectS. Call from loop().
void tick();

// Notify an unsolicited status Response (seq = 0) to the connected app, if any.
void notifyStatus();

}  // namespace ble_service
