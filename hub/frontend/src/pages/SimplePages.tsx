import { useEffect, useState } from "react";

const copy: Record<string, [string, string]> = {
  photos: ["Manage Photos", "Upload, process, queue, shuffle, and publish ePaper-ready photo frames."],
  dashboards: ["Dashboards", "Edit 2 x 4 tile layouts, bind widgets to Home Assistant, and preview output."],
  devices: ["Devices", "Track battery, firmware, last refresh, mesh status, and selected display content."],
  "home-assistant": ["Home Assistant", "Paste a long-lived access token, validate it, and cache entity metadata."],
  settings: ["Settings", "Configure local auth, refresh intervals, data paths, and display defaults."],
  updates: ["Updates", "Check GitHub Releases, back up before updating, and approve firmware releases."],
  diagnostics: ["Diagnostics", "Inspect Thread reachability, service health, logs, and simulator state."]
};

export function SimplePage({ route }: { route: keyof typeof copy }) {
  if (route === "updates") {
    return <UpdatesPage />;
  }
  const [title, description] = copy[route];
  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </header>
      <section className="empty-state">
        <h2>{title} workspace</h2>
        <p>This route is scaffolded for the Phase implementation behind the current API contract.</p>
        <button className="secondary-button">Open settings</button>
      </section>
    </div>
  );
}

type HubUpdateStatus = {
  status: string;
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  repository: string | null;
  release_url?: string | null;
  error?: string | null;
};

type AutoUpdateStatus = {
  configured: boolean;
  auto_apply: boolean;
  apply_allowed: boolean;
  check_interval_seconds: number;
  command: string;
};

type FirmwareStatus = {
  status: string;
  board: string;
  latest_version: string | null;
  update_available: boolean;
  sha256?: string | null;
  error?: string | null;
};

function UpdatesPage() {
  const [hub, setHub] = useState<HubUpdateStatus | null>(null);
  const [auto, setAuto] = useState<AutoUpdateStatus | null>(null);
  const [firmware, setFirmware] = useState<FirmwareStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/api/updates/hub/check").then((response) => response.json()),
      fetch("/api/updates/hub/auto").then((response) => response.json()),
      fetch("/api/updates/firmware/manifest?board=xiao_mg24").then((response) => response.json())
    ])
      .then(([hubStatus, autoStatus, firmwareStatus]) => {
        setHub(hubStatus);
        setAuto(autoStatus);
        setFirmware(firmwareStatus);
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load update status."));
  }, []);

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>Updates</h1>
          <p>Check GitHub Releases, back up before updating, and approve firmware releases.</p>
        </div>
      </header>
      {error && <section className="empty-state"><p>{error}</p></section>}
      <section className="update-grid">
        <UpdatePanel
          title="Hub"
          status={hub?.status ?? "loading"}
          rows={[
            ["Current", hub?.current_version ?? "Loading"],
            ["Latest", hub?.latest_version ?? "Not found"],
            ["Repository", hub?.repository ?? "Not configured"],
            ["Auto apply", auto ? (auto.auto_apply && auto.apply_allowed ? "Enabled" : "Disabled") : "Loading"],
            ["Command", auto?.command ?? "Loading"]
          ]}
          detail={hub?.error ?? (hub?.update_available ? "A newer release is available." : "No hub update is pending.")}
        />
        <UpdatePanel
          title="Firmware"
          status={firmware?.status ?? "loading"}
          rows={[
            ["Board", firmware?.board ?? "xiao_mg24"],
            ["Latest", firmware?.latest_version ?? "Not found"],
            ["Checksum", firmware?.sha256 ? "Present" : "Missing"],
            ["Delivery", "Hub mediated"]
          ]}
          detail={firmware?.error ?? "Devices pull this manifest after battery and hardware checks pass."}
        />
      </section>
    </div>
  );
}

function UpdatePanel({
  title,
  status,
  rows,
  detail
}: {
  title: string;
  status: string;
  rows: Array<[string, string]>;
  detail: string;
}) {
  const tone = status === "current" ? "status-good" : status === "update_available" ? "status-warn" : "status-neutral";
  return (
    <section className="update-panel">
      <div className="preview-toolbar">
        <div>
          <h2>{title}</h2>
          <p>{detail}</p>
        </div>
        <span className={`status-badge ${tone}`}>{status}</span>
      </div>
      <dl className="update-list">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
