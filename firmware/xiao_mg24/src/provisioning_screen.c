#include "provisioning_screen.h"

inkdaddy_display_content_kind_t inkdaddy_next_display_content(bool commissioned, bool mesh_connected, uint16_t cycleable_content_count, uint32_t refresh_count, bool provisioning_requested) {
  if (commissioned && mesh_connected && !provisioning_requested) {
    return INKDADDY_DISPLAY_NORMAL_FRAME;
  }
  if (cycleable_content_count == 0) {
    return INKDADDY_DISPLAY_MATTER_JOIN_SCREEN;
  }
  if ((refresh_count % 2U) == 0U) {
    return INKDADDY_DISPLAY_MATTER_JOIN_SCREEN;
  }
  return INKDADDY_DISPLAY_NORMAL_FRAME;
}
