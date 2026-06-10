#include "frame_client.h"

bool inkdaddy_fetch_frame_manifest(inkdaddy_frame_manifest_t *manifest) {
  (void)manifest;
  return false;
}

bool inkdaddy_download_frame(const inkdaddy_frame_manifest_t *manifest, uint8_t *buffer, size_t buffer_len) {
  (void)manifest;
  (void)buffer;
  (void)buffer_len;
  return false;
}

bool inkdaddy_verify_frame_sha256(const inkdaddy_frame_manifest_t *manifest, const uint8_t *buffer, size_t buffer_len) {
  (void)manifest;
  (void)buffer;
  (void)buffer_len;
  return false;
}
