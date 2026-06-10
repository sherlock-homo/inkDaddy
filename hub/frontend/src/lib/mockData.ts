import type { DisplayStatus } from "./types";

export const display: DisplayStatus = {
  name: "Kitchen Frame",
  batteryPercent: 87,
  lastRefresh: "12 min ago",
  nextWake: "18 min",
  activeMode: "Home Overview + Family Photos",
  meshConnected: false,
  provisioned: false
};

export const navItems = [
  ["home", "Home"],
  ["connect", "Connect inkDaddy"],
  ["photos", "Manage Photos"],
  ["dashboards", "Dashboards"],
  ["integrations", "Integrations"],
  ["devices", "Devices"],
  ["home-assistant", "Home Assistant"],
  ["settings", "Settings"],
  ["updates", "Updates"],
  ["diagnostics", "Diagnostics"]
] as const;
