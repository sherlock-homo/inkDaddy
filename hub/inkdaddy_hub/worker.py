from __future__ import annotations

import json
import signal
import time

from .config import get_settings
from .services.updates import run_auto_update_cycle


def main() -> None:
    running = True
    settings = get_settings()
    interval = max(300, settings.update_check_interval_seconds)
    last_update_check = 0.0

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while running:
        now = time.monotonic()
        if now - last_update_check >= interval:
            last_update_check = now
            result = run_auto_update_cycle(settings)
            if result.get("status") not in {"disabled", "current"}:
                print(f"[inkDaddy worker] auto-update: {json.dumps(result, sort_keys=True)}", flush=True)
        time.sleep(min(30, interval))


if __name__ == "__main__":
    main()
