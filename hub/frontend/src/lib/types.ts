export type RouteKey =
  | "home"
  | "connect"
  | "photos"
  | "dashboards"
  | "integrations"
  | "devices"
  | "home-assistant"
  | "settings"
  | "updates"
  | "diagnostics";

export interface DisplayStatus {
  name: string;
  batteryPercent: number;
  lastRefresh: string;
  nextWake: string;
  activeMode: string;
  meshConnected: boolean;
  provisioned: boolean;
}

export interface PhotoRecord {
  id: string;
  original_filename: string;
  processed_status: string;
  width: number | null;
  height: number | null;
  palette: string | null;
  checksum: string | null;
  preview_url: string | null;
  frame_url: string | null;
  uploaded_at: string | null;
}

export interface AlbumRecord {
  id: string;
  name: string;
  mode: string;
  item_count: number;
}

export interface DeviceRecord {
  id: string;
  device_uid: string;
  name: string;
  hardware_target: string;
  firmware_version: string | null;
  provisioned: boolean;
  mesh_connected: boolean;
  refresh_interval_minutes: number;
  refresh_interval_warning: boolean;
  selected_source_type: string;
  selected_source_id: string | null;
  last_seen_at: string | null;
  last_refresh_result: string | null;
  last_frame_id: string | null;
  battery_percent: number | null;
  battery_voltage: number | null;
}

export interface DeviceHistoryRecord {
  status: string;
  battery_percent: number | null;
  battery_voltage: number | null;
  created_at: string;
}

export interface HAConfig {
  base_url: string;
  configured: boolean;
  enabled: boolean;
  last_validated_at: string | null;
  token_preview: string | null;
  token_page_url: string;
  entity_count: number;
}

export interface HAEntity {
  entity_id: string;
  domain: string;
  name: string | null;
  state: string | null;
  attributes: Record<string, unknown>;
  updated_at: string | null;
}

export interface IntegrationRecord {
  id: string;
  name: string;
  status: string;
  configured: boolean;
  enabled: boolean;
  entity_count?: number;
  device_count?: number;
  manage_url: string;
}
