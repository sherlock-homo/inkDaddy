# XIAO MG24 Firmware Build, Flash, And OTA

The primary firmware path is Silicon Labs SiSDK / Matter Extension using SLC-CLI.
Zephyr is not part of the v1 implementation path.

Target responsibilities:

- Matter/BLE provisioning and Thread join/resume.
- CoAP blockwise or chunked UDP frame transfer over Thread IPv6.
- ePaper SPI HAL for reset, busy, data/command, chip select, and optional power.
- Battery ADC, status heartbeat, refresh result reporting, and deep sleep.
- Matter control/status clusters where feasible after MVP validation.
- Rollback-safe OTA using the Silicon Labs bootloader path.

The checked-in firmware folder is a SiSDK-oriented skeleton. Generate the final
project with installed Silicon Labs tooling, then keep product logic in the
`src/inkdaddy_*` modules.

Validate the checked-in scaffold without SiSDK:

```bash
python3 firmware/xiao_mg24/tools/validate_sisdk.py
```

Validate on the SiSDK build machine:

```bash
python3 firmware/xiao_mg24/tools/validate_sisdk.py --strict-tools --strict-host-compile --require-slcp
```

Expected strict prerequisites:

- SLC-CLI available as `slc`.
- Simplicity Commander available as `commander` or `simplicitycommander`.
- ARM toolchain available as `arm-none-eabi-gcc`.
- Working host C compiler for portable module validation.
- A generated SiSDK `.slcp` project in `firmware/xiao_mg24/`.

If strict validation reports that no `.slcp` file exists, generate the vendor
project with Silicon Labs Simplicity Studio or SLC-CLI, then add the inkDaddy
modules from `src/` into that project. Keep the full-frame transfer out of
Matter attributes; use OpenThread IPv6 data-plane code for CoAP blockwise or
chunked UDP frame pulls.

## Firmware OTA Contract

The hub exposes firmware metadata at:

```text
GET /api/updates/firmware/manifest?board=xiao_mg24&current_version=<device-version>
```

The device must only stage a firmware update when all gates pass:

- Board/hardware target matches `xiao_mg24`.
- Battery is at or above `battery_threshold_percent`, or external power is
  present.
- The artifact has a SHA-256 checksum or future signature.
- The SiSDK/Gecko Bootloader slot is rollback-capable.

The checked-in `src/ota_client.*` files define these gates and the integration
points for fetching the manifest, downloading the `.gbl` artifact over Thread,
staging it into Gecko Bootloader storage, and marking the new image as confirmed
after a successful boot.

Release assets should include:

```text
inkdaddy-firmware-xiao_mg24-vX.Y.Z.gbl
inkdaddy-firmware-xiao_mg24-vX.Y.Z.gbl.sha256
inkdaddy-firmware-xiao_mg24-vX.Y.Z.json
```

Build the source and optional firmware release assets with:

```bash
INKDADDY_FIRMWARE_BINARY=firmware/xiao_mg24/build/inkdaddy.gbl \
  ./scripts/build_release_assets.sh vX.Y.Z
```

Hardware validation remains open until the generated SiSDK project is built and
flashed on a Seeed XIAO MG24 board with the final bootloader configuration.
