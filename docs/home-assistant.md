# Home Assistant Integration

inkDaddy starts without Home Assistant configured.

1. Open `http://homeassistant.local:8123/profile` or the profile page for your
   manually entered Home Assistant URL.
2. Create a long-lived access token.
3. Paste the token into `inkDaddy > Home Assistant`.
4. inkDaddy validates the token against the Home Assistant REST API.
5. Entity metadata is cached locally for dashboard widget binding.

Do not place Home Assistant tokens in dashboard YAML. Tokens are stored in the
restricted secrets file and are redacted from diagnostics and logs.
