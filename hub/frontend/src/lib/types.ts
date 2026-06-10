export type RouteKey =
  | "home"
  | "connect"
  | "photos"
  | "dashboards"
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
