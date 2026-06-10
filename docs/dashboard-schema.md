# Dashboard Schema

Dashboards use a fixed 4 column x 2 row logical grid for the default 7.3 inch
800 x 480 target.

```yaml
version: 1
name: Home Overview
target:
  width: 800
  height: 480
  palette: waveshare_7color_6
grid:
  cols: 4
  rows: 2
widgets:
  - id: living_room_temp
    type: big_number
    x: 0
    y: 0
    w: 1
    h: 1
    source:
      type: home_assistant
      entity_id: sensor.living_room_temperature
    options:
      label: Living Room
      unit: F
```

The validator rejects unsupported widget types, invalid footprints, out-of-grid
widgets, and tile overlaps.
