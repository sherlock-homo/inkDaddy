# Display Pairing And Provisioning

The XIAO MG24 display enters provisioning mode when it is not commissioned or
cannot rejoin the Thread mesh within the startup window.

Provisioning display behavior:

- Show a Matter QR code on the ePaper display.
- Show the manual setup code, setup PIN, and discriminator.
- Include short instructions: scan to add inkDaddy display and confirm a Thread
  Border Router is available.
- If queued photos/dashboard frames exist while unjoined, alternate every other
  refresh between content and the Matter join screen.
- If no cycleable content exists, show only the join screen.

Pairing credentials are intentionally visible on the physical display during
provisioning, but must not be printed in normal logs or diagnostics.
