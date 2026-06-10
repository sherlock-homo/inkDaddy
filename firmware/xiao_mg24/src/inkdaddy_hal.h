#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

typedef enum {
  INKDADDY_HAL_OK = 0,
  INKDADDY_HAL_ERR = 1,
  INKDADDY_HAL_TIMEOUT = 2,
} inkdaddy_hal_status_t;

typedef struct {
  uint16_t width;
  uint16_t height;
  uint8_t bits_per_pixel;
  const char *palette_name;
} inkdaddy_frame_format_t;

void inkdaddy_log_boot(void);
inkdaddy_hal_status_t inkdaddy_epaper_init(void);
inkdaddy_hal_status_t inkdaddy_epaper_refresh(const uint8_t *packed_frame, size_t frame_len, inkdaddy_frame_format_t format);
inkdaddy_hal_status_t inkdaddy_epaper_render_join_screen(const char *qr_payload, const char *setup_pin, const char *manual_code, const char *discriminator);
uint16_t inkdaddy_battery_millivolts(void);
uint8_t inkdaddy_battery_percent(void);
void inkdaddy_sleep_minutes(uint16_t minutes);
