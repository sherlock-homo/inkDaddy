# GitHub Releases

Hub releases should include:

- Source/package archive.
- Checksums.
- Version metadata.
- Migration notes.

Firmware releases should include:

- XIAO MG24 firmware binary.
- Board/hardware compatibility metadata.
- Checksum or signature.
- Release notes.
- Minimum bootloader requirements.

Example:

```bash
./scripts/build_release_assets.sh v0.1.0

gh release create v0.1.0 \
  dist/releases/inkdaddy-v0.1.0.tar.gz \
  dist/releases/inkdaddy-v0.1.0.tar.gz.sha256 \
  --title "inkDaddy v0.1.0" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

Firmware assets can be included when the SiSDK build produces a Gecko Bootloader
image:

```bash
INKDADDY_FIRMWARE_BINARY=firmware/xiao_mg24/build/inkdaddy.gbl \
  ./scripts/build_release_assets.sh v0.1.0

gh release upload v0.1.0 \
  dist/releases/inkdaddy-firmware-xiao_mg24-v0.1.0.gbl \
  dist/releases/inkdaddy-firmware-xiao_mg24-v0.1.0.gbl.sha256 \
  dist/releases/inkdaddy-firmware-xiao_mg24-v0.1.0.json
```

The hub reads GitHub Release metadata using:

```text
GET https://api.github.com/repos/{owner}/{repo}/releases/latest
```

For private repositories, configure a read-only token in the LXC service
environment. Do not put GitHub tokens into dashboard YAML, release notes, or
diagnostic logs.

## Push-Driven Update Pattern

For a push-to-update workflow, add CI that runs tests, builds release assets, and
creates or updates a release when a tag is pushed:

```bash
git tag v0.1.1
git push origin v0.1.1
./scripts/build_release_assets.sh v0.1.1
gh release create v0.1.1 dist/releases/inkdaddy-v0.1.1.tar.gz \
  dist/releases/inkdaddy-v0.1.1.tar.gz.sha256 \
  --generate-notes \
  --latest
```

Once the release exists, installed hubs with `INKDADDY_AUTO_UPDATE=1` and
`INKDADDY_UPDATE_ALLOW_APPLY=1` will pick it up on the next worker interval.
