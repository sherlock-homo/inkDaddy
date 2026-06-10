#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum {
  INKDADDY_OTA_IDLE = 0,
  INKDADDY_OTA_UPDATE_AVAILABLE,
  INKDADDY_OTA_BLOCKED_LOW_BATTERY,
  INKDADDY_OTA_BLOCKED_HARDWARE_MISMATCH,
  INKDADDY_OTA_BLOCKED_MISSING_CHECKSUM,
  INKDADDY_OTA_DOWNLOADING,
  INKDADDY_OTA_READY_TO_APPLY,
  INKDADDY_OTA_APPLYING,
  INKDADDY_OTA_FAILED
} inkdaddy_ota_state_t;

typedef struct {
  char version[33];
  char board[33];
  char artifact_url[192];
  char sha256[65];
  uint32_t size_bytes;
  uint8_t battery_threshold_percent;
  bool requires_external_power;
} inkdaddy_firmware_manifest_t;

typedef struct {
  uint8_t battery_percent;
  bool external_power_present;
  char board[33];
  char current_version[33];
} inkdaddy_ota_context_t;

bool inkdaddy_ota_manifest_is_safe(const inkdaddy_firmware_manifest_t *manifest,
                                   const inkdaddy_ota_context_t *context,
                                   inkdaddy_ota_state_t *blocked_reason);
bool inkdaddy_ota_fetch_manifest(inkdaddy_firmware_manifest_t *manifest);
bool inkdaddy_ota_download_and_stage(const inkdaddy_firmware_manifest_t *manifest);
bool inkdaddy_ota_mark_boot_success(void);
