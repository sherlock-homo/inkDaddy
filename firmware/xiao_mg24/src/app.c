#include "frame_client.h"
#include "inkdaddy_hal.h"
#include "ota_client.h"
#include "provisioning_screen.h"
#include "../config/inkdaddy_config.h"

void inkdaddy_app_main(void) {
  inkdaddy_log_boot();
  (void)inkdaddy_epaper_init();

  /*
   * SiSDK integration points to wire after project generation:
   * - Matter commissioning window / QR payload retrieval.
   * - OpenThread role and mesh connectivity.
   * - CoAP blockwise or UDP chunk transfer.
   * - Gecko bootloader OTA state.
   */
  inkdaddy_ota_context_t ota_context = {
    .battery_percent = 0,
    .external_power_present = false,
  };
  (void)ota_context;
}
