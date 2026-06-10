#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
  char frame_id[33];
  char sha256[65];
  char palette[32];
  uint32_t size_bytes;
  uint16_t width;
  uint16_t height;
  uint8_t bits_per_pixel;
  bool changed;
} inkdaddy_frame_manifest_t;

bool inkdaddy_fetch_frame_manifest(inkdaddy_frame_manifest_t *manifest);
bool inkdaddy_download_frame(const inkdaddy_frame_manifest_t *manifest, uint8_t *buffer, size_t buffer_len);
bool inkdaddy_verify_frame_sha256(const inkdaddy_frame_manifest_t *manifest, const uint8_t *buffer, size_t buffer_len);
