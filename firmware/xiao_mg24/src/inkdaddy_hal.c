#include "inkdaddy_hal.h"

void inkdaddy_log_boot(void) {
  /* Route to Silicon Labs logging once the SiSDK project is generated. */
}

inkdaddy_hal_status_t inkdaddy_epaper_init(void) {
  return INKDADDY_HAL_OK;
}

inkdaddy_hal_status_t inkdaddy_epaper_refresh(const uint8_t *packed_frame, size_t frame_len, inkdaddy_frame_format_t format) {
  (void)packed_frame;
  (void)frame_len;
  (void)format;
  return INKDADDY_HAL_OK;
}

inkdaddy_hal_status_t inkdaddy_epaper_render_join_screen(const char *qr_payload, const char *setup_pin, const char *manual_code, const char *discriminator) {
  (void)qr_payload;
  (void)setup_pin;
  (void)manual_code;
  (void)discriminator;
  return INKDADDY_HAL_OK;
}

uint16_t inkdaddy_battery_millivolts(void) {
  return 0;
}

uint8_t inkdaddy_battery_percent(void) {
  return 0;
}

void inkdaddy_sleep_minutes(uint16_t minutes) {
  (void)minutes;
}
