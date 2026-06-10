#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request


def post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate an inkDaddy display client.")
    parser.add_argument("--hub", default="http://127.0.0.1:8080")
    parser.add_argument("--device", default="sim-xiao-mg24-001")
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--joined", action="store_true")
    args = parser.parse_args()

    post_json(
        f"{args.hub}/api/simulator/devices",
        {
            "device_uid": args.device,
            "provisioned": args.joined,
            "mesh_connected": args.joined,
            "battery_percent": 87,
        },
    )
    for refresh_count in range(args.cycles):
        post_json(
            f"{args.hub}/api/devices/{args.device}/heartbeat",
            {"battery_percent": 87, "mesh_connected": args.joined, "timestamp": time.time()},
        )
        manifest = get_json(f"{args.hub}/api/devices/{args.device}/frame-manifest?refresh_count={refresh_count}")
        with urllib.request.urlopen(f"{args.hub}{manifest['download_url']}", timeout=10) as response:
            frame = response.read()
        post_json(
            f"{args.hub}/api/devices/{args.device}/refresh-result",
            {"result": "displayed", "frame_id": manifest["frame_id"], "bytes": len(frame)},
        )
        print(f"{refresh_count}: {manifest['content_kind']} {manifest['frame_id']} {len(frame)} bytes")


if __name__ == "__main__":
    main()
