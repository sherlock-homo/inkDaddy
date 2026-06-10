#include "ota_client.h"

#include <string.h>

#include "../config/inkdaddy_config.h"

bool inkdaddy_ota_manifest_is_safe(const inkdaddy_firmware_manifest_t *manifest,
                                   const inkdaddy_ota_context_t *context,
                                   inkdaddy_ota_state_t *blocked_reason) {
  if (blocked_reason != NULL) {
    *blocked_reason = INKDADDY_OTA_IDLE;
  }
  if (manifest == NULL || context == NULL) {
    if (blocked_reason != NULL) {
      *blocked_reason = INKDADDY_OTA_FAILED;
    }
    return false;
  }
  if (strncmp(manifest->board, context->board, sizeof(manifest->board)) != 0) {
    if (blocked_reason != NULL) {
      *blocked_reason = INKDADDY_OTA_BLOCKED_HARDWARE_MISMATCH;
    }
    return false;
  }
  if (manifest->sha256[0] == '\0') {
    if (blocked_reason != NULL) {
      *blocked_reason = INKDADDY_OTA_BLOCKED_MISSING_CHECKSUM;
    }
    return false;
  }
  if (!context->external_power_present &&
      context->battery_percent < manifest->battery_threshold_percent) {
    if (blocked_reason != NULL) {
      *blocked_reason = INKDADDY_OTA_BLOCKED_LOW_BATTERY;
    }
    return false;
  }
  return true;
}

bool inkdaddy_ota_fetch_manifest(inkdaddy_firmware_manifest_t *manifest) {
  /*
   * SiSDK integration point:
   * - Fetch INKDADDY_OTA_MANIFEST_PATH from the hub over Thread IPv6.
   * - Parse JSON fields into inkdaddy_firmware_manifest_t.
   * - Do not print the full artifact URL if it carries signed access tokens.
   */
  (void)manifest;
  return false;
}

bool inkdaddy_ota_download_and_stage(const inkdaddy_firmware_manifest_t *manifest) {
  /*
   * SiSDK integration point:
   * - Download the .gbl artifact over the Thread data plane.
   * - Stream to the Gecko Bootloader storage slot.
   * - Verify SHA-256 before requesting bootloader apply.
   * - Leave the previous image bootable until the new image confirms boot.
   */
  (void)manifest;
  return false;
}

bool inkdaddy_ota_mark_boot_success(void) {
  /*
   * SiSDK integration point:
   * - Mark the newly booted image as confirmed after app initialization,
   *   Thread resume, and basic hub heartbeat succeed.
   */
  return false;
}
