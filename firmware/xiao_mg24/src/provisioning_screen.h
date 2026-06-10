#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef enum {
  INKDADDY_DISPLAY_NORMAL_FRAME = 0,
  INKDADDY_DISPLAY_MATTER_JOIN_SCREEN = 1,
} inkdaddy_display_content_kind_t;

inkdaddy_display_content_kind_t inkdaddy_next_display_content(bool commissioned, bool mesh_connected, uint16_t cycleable_content_count, uint32_t refresh_count, bool provisioning_requested);
