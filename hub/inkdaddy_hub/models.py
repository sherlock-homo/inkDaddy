from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Setting(Base, TimestampMixin):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)


class SetupState(Base, TimestampMixin):
    __tablename__ = "setup_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admin_password_hash: Mapped[str | None] = mapped_column(String(255))


class HomeAssistantConfig(Base, TimestampMixin):
    __tablename__ = "home_assistant_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    token_secret_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime)


class HAEntityCache(Base, TimestampMixin):
    __tablename__ = "ha_entity_cache"

    entity_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    device_id: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(255))
    attributes_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class Dashboard(Base, TimestampMixin):
    __tablename__ = "dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    yaml_path: Mapped[str | None] = mapped_column(String(1024))
    current_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    target_width: Mapped[int] = mapped_column(Integer, default=800, nullable=False)
    target_height: Mapped[int] = mapped_column(Integer, default=480, nullable=False)
    palette: Mapped[str] = mapped_column(String(64), default="waveshare_7color_6", nullable=False)

    versions: Mapped[list["DashboardVersion"]] = relationship(back_populates="dashboard")


class DashboardVersion(Base, TimestampMixin):
    __tablename__ = "dashboard_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    yaml: Mapped[str] = mapped_column(Text, nullable=False)

    dashboard: Mapped[Dashboard] = relationship(back_populates="versions")


class Photo(Base, TimestampMixin):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    original_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    processed_path: Mapped[str | None] = mapped_column(String(1024))
    preview_path: Mapped[str | None] = mapped_column(String(1024))
    frame_path: Mapped[str | None] = mapped_column(String(1024))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    palette: Mapped[str | None] = mapped_column(String(64))
    checksum: Mapped[str | None] = mapped_column(String(128))
    processed_status: Mapped[str] = mapped_column(String(64), default="pending", nullable=False)


class Album(Base, TimestampMixin):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), default="ordered", nullable=False)


class AlbumItem(Base, TimestampMixin):
    __tablename__ = "album_items"
    __table_args__ = (UniqueConstraint("album_id", "photo_id", name="uq_album_photo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), nullable=False)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hardware_target: Mapped[str] = mapped_column(String(128), default="xiao_mg24", nullable=False)
    firmware_version: Mapped[str | None] = mapped_column(String(64))
    hardware_version: Mapped[str | None] = mapped_column(String(64))
    provisioned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mesh_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refresh_interval_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    selected_source_type: Mapped[str] = mapped_column(String(32), default="dashboard", nullable=False)
    selected_source_id: Mapped[str | None] = mapped_column(String(128))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_refresh_result: Mapped[str | None] = mapped_column(String(64))
    last_frame_id: Mapped[str | None] = mapped_column(String(128))
    battery_percent: Mapped[float | None] = mapped_column(Float)
    battery_voltage: Mapped[float | None] = mapped_column(Float)
    commissioning_secret_ref: Mapped[str | None] = mapped_column(String(255))


class DeviceStatusHistory(Base, TimestampMixin):
    __tablename__ = "device_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    battery_percent: Mapped[float | None] = mapped_column(Float)
    battery_voltage: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class Frame(Base, TimestampMixin):
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    frame_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    palette: Mapped[str] = mapped_column(String(64), nullable=False)
    bits_per_pixel: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    packing: Mapped[str] = mapped_column(String(64), default="high_nibble_first", nullable=False)
    byte_order: Mapped[str] = mapped_column(String(32), default="row_major", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(128), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream", nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)


class DisplayAssignment(Base, TimestampMixin):
    __tablename__ = "display_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    cycle_mode: Mapped[str] = mapped_column(String(32), default="ordered", nullable=False)


class UpdateCheck(Base, TimestampMixin):
    __tablename__ = "update_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    current_version: Mapped[str] = mapped_column(String(64), nullable=False)
    latest_version: Mapped[str | None] = mapped_column(String(64))
    release_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)


class FirmwareRelease(Base, TimestampMixin):
    __tablename__ = "firmware_releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    board: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    release_notes: Mapped[str | None] = mapped_column(Text)
    min_bootloader_version: Mapped[str | None] = mapped_column(String(64))


class JobRun(Base, TimestampMixin):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    log_path: Mapped[str | None] = mapped_column(String(1024))
    detail_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
