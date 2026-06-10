# inkDaddy XIAO MG24 Firmware

Primary target: Seeed XIAO MG24 using Silicon Labs SiSDK / Matter Extension and
SLC-CLI.

This folder intentionally does not contain Zephyr scaffolding. Generate the
vendor project with Silicon Labs tooling, then keep inkDaddy product logic in
the `src/` modules here.

Local static validation:

```bash
python3 firmware/xiao_mg24/tools/validate_sisdk.py
```

Full SiSDK build-machine validation:

```bash
python3 firmware/xiao_mg24/tools/validate_sisdk.py --strict-tools --strict-host-compile --require-slcp
```

The strict command expects SLC-CLI, Simplicity Commander, `arm-none-eabi-gcc`,
working host C compilation, and a generated `.slcp` project in this directory.
Until the Silicon Labs project is generated on a machine with SiSDK installed,
the checked-in sources are validated as portable product modules only.

MVP behavior:

1. Boot and initialize logging.
2. Resume or join Thread.
3. If not commissioned or mesh join fails within about 30 seconds, enter
   provisioning for 5 minutes.
4. Render Matter QR/manual code/discriminator on ePaper while provisioning.
5. If cycleable content exists while unjoined, alternate every other refresh
   between content and join screen.
6. Report battery/status to hub.
7. Fetch frame manifest.
8. Download frame over CoAP blockwise or chunked UDP.
9. Verify SHA-256.
10. Refresh ePaper.
11. Report result.
12. Enter deep sleep.

Matter is the control/status plane. Full ePaper frames are never sent through
normal Matter attributes or command payloads.

Firmware OTA is hub mediated. The device checks
`/api/updates/firmware/manifest?board=xiao_mg24`, verifies board, battery or
external power, checksum, and rollback-capable bootloader state, then stages the
`.gbl` artifact through the SiSDK/Gecko Bootloader integration points in
`src/ota_client.*`.
