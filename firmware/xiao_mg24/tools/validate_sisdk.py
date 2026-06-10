#!/usr/bin/env python3
"""Validate the XIAO MG24 SiSDK firmware scaffold.

This script deliberately separates static repo validation from real Silicon
Labs toolchain validation. The default mode is useful on developer machines and
CI runners without SiSDK installed. Use --strict-tools on the firmware build
machine to require SLC-CLI, Commander, and the ARM GCC toolchain.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = FIRMWARE_ROOT / "src"
CONFIG_DIR = FIRMWARE_ROOT / "config"

REQUIRED_FILES = [
    FIRMWARE_ROOT / "README.md",
    CONFIG_DIR / "inkdaddy_config.h",
    SRC_DIR / "app.c",
    SRC_DIR / "frame_client.c",
    SRC_DIR / "frame_client.h",
    SRC_DIR / "inkdaddy_hal.c",
    SRC_DIR / "inkdaddy_hal.h",
    SRC_DIR / "ota_client.c",
    SRC_DIR / "ota_client.h",
    SRC_DIR / "provisioning_screen.c",
    SRC_DIR / "provisioning_screen.h",
]


def check_required_files() -> list[str]:
    return [f"missing required file: {path.relative_to(FIRMWARE_ROOT)}" for path in REQUIRED_FILES if not path.exists()]


def run_version(tool: str) -> str:
    try:
        result = subprocess.run(
            [tool, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"{tool}: unable to run --version ({exc})"
    output = (result.stdout or result.stderr).strip().splitlines()
    first_line = output[0] if output else f"exit {result.returncode}"
    return f"{tool}: {first_line}"


def find_tool(candidates: list[str]) -> str | None:
    for name in candidates:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def check_tools(strict: bool) -> tuple[list[str], list[str]]:
    messages: list[str] = []
    errors: list[str] = []
    tools = {
        "SLC-CLI": ["slc"],
        "Simplicity Commander": ["commander", "simplicitycommander"],
        "ARM GCC": ["arm-none-eabi-gcc"],
    }
    for label, candidates in tools.items():
        resolved = find_tool(candidates)
        if resolved:
            messages.append(run_version(resolved))
        else:
            message = f"missing {label}: expected one of {', '.join(candidates)} on PATH"
            messages.append(message)
            if strict:
                errors.append(message)
    return messages, errors


def host_compile_portable_sources() -> tuple[list[str], list[str]]:
    messages: list[str] = []
    cc = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if not cc:
        messages.append("warning: missing host C compiler; skipped portable C compile check")
        return messages, []
    with tempfile.TemporaryDirectory(prefix="inkdaddy-fw-") as tmpdir:
        obj = Path(tmpdir) / "provisioning_screen.o"
        cmd = [
            cc,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(SRC_DIR),
            "-I",
            str(CONFIG_DIR),
            "-c",
            str(SRC_DIR / "provisioning_screen.c"),
            "-o",
            str(obj),
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        messages.append(f"warning: host compile failed for provisioning_screen.c: {detail}")
        return messages, [messages[-1]]
    messages.append("host compile passed for provisioning_screen.c")
    return messages, []


def check_slcp_presence(strict: bool) -> list[str]:
    projects = sorted(FIRMWARE_ROOT.glob("*.slcp"))
    if projects:
        return [f"found SiSDK project file: {projects[0].name}"]
    message = "no .slcp project file yet; generate it with Silicon Labs SLC-CLI/Simplicity Studio before hardware build"
    return [f"ERROR: {message}" if strict else f"warning: {message}"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate inkDaddy XIAO MG24 SiSDK scaffold")
    parser.add_argument(
        "--strict-tools",
        action="store_true",
        help="fail if SLC-CLI, Commander, or arm-none-eabi-gcc are missing",
    )
    parser.add_argument(
        "--strict-host-compile",
        action="store_true",
        help="fail if the portable C host compile check cannot run cleanly",
    )
    parser.add_argument(
        "--require-slcp",
        action="store_true",
        help="fail if a generated SiSDK .slcp project file is not present",
    )
    args = parser.parse_args()

    errors = check_required_files()
    host_messages, host_errors = host_compile_portable_sources()
    if args.strict_host_compile:
        errors.extend(host_errors)
    tool_messages, tool_errors = check_tools(args.strict_tools)
    errors.extend(tool_errors)
    slcp_messages = check_slcp_presence(args.require_slcp)
    if args.require_slcp:
        errors.extend(message[7:] for message in slcp_messages if message.startswith("ERROR: "))

    print("inkDaddy XIAO MG24 SiSDK validation")
    print(f"firmware root: {FIRMWARE_ROOT}")
    for message in host_messages + tool_messages + slcp_messages:
        print(f"- {message}")

    if errors:
        print("\nValidation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nStatic firmware validation passed.")
    if not args.strict_tools:
        print("Run again with --strict-tools --strict-host-compile on the SiSDK build machine for full toolchain validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
