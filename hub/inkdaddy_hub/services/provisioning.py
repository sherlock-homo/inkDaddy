from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DisplayContentKind(str, Enum):
    NORMAL_FRAME = "normal_frame"
    MATTER_JOIN_SCREEN = "matter_join_screen"


@dataclass(frozen=True)
class ProvisioningState:
    commissioned: bool
    mesh_connected: bool
    cycleable_content_count: int
    refresh_count: int
    provisioning_requested: bool = False


def next_display_content_kind(state: ProvisioningState) -> DisplayContentKind:
    """Choose what an unjoined display should show on its next ePaper refresh.

    Joined devices always show normal content. Unjoined devices with content alternate
    normal frame, join screen, normal frame, join screen. Unjoined devices without
    content show only the Matter join screen.
    """

    if state.commissioned and state.mesh_connected and not state.provisioning_requested:
        return DisplayContentKind.NORMAL_FRAME
    if state.cycleable_content_count <= 0:
        return DisplayContentKind.MATTER_JOIN_SCREEN
    if state.refresh_count % 2 == 0:
        return DisplayContentKind.MATTER_JOIN_SCREEN
    return DisplayContentKind.NORMAL_FRAME


def should_enter_provisioning(
    *,
    commissioned: bool,
    mesh_connected: bool,
    seconds_since_boot: int,
    startup_join_timeout_seconds: int = 30,
) -> bool:
    if commissioned and mesh_connected:
        return False
    return seconds_since_boot >= startup_join_timeout_seconds
