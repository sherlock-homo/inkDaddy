import { useEffect, useState } from "react";
import { apiJson } from "../lib/api";
import type { DeviceHistoryRecord, DeviceRecord } from "../lib/types";

export function DevicesPage() {
  const [devices, setDevices] = useState<DeviceRecord[]>([]);
  const [history, setHistory] = useState<Record<string, DeviceHistoryRecord[]>>({});
  const [name, setName] = useState("Kitchen Frame");
  const [uid, setUid] = useState("sim-xiao-mg24-001");
  const [message, setMessage] = useState("Ready");

  const load = async () => {
    const payload = await apiJson<{ devices: DeviceRecord[] }>("/api/devices");
    setDevices(payload.devices);
    const historyPairs = await Promise.all(
      payload.devices.map(async (device) => {
        const item = await apiJson<{ history: DeviceHistoryRecord[] }>(`/api/devices/${device.device_uid}/history?limit=3`);
        return [device.device_uid, item.history] as const;
      })
    );
    setHistory(Object.fromEntries(historyPairs));
  };

  useEffect(() => {
    load().catch((error: Error) => setMessage(error.message));
  }, []);

  const createSimulator = async () => {
    const payload = await apiJson<{ device: DeviceRecord }>("/api/simulator/devices", {
      method: "POST",
      body: JSON.stringify({ device_uid: uid, name, provisioned: false, mesh_connected: false })
    });
    setMessage(`Created ${payload.device.name}.`);
    await load();
  };

  const updateDevice = async (device: DeviceRecord, patch: Partial<DeviceRecord>) => {
    await apiJson(`/api/devices/${device.device_uid}`, {
      method: "PUT",
      body: JSON.stringify(patch)
    });
    await load();
  };

  const forceManifest = async (device: DeviceRecord) => {
    const manifest = await apiJson<{ frame_id: string; content_kind: string }>(
      `/api/devices/${device.device_uid}/frame-manifest?refresh_count=0`
    );
    setMessage(`${device.name} prepared ${manifest.content_kind} frame ${manifest.frame_id}.`);
    await load();
  };

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>Devices</h1>
          <p>Register displays, track battery and mesh state, and choose what each display pulls when it wakes.</p>
        </div>
      </header>

      <section className="workflow-panel">
        <div className="form-row">
          <label>
            Device UID
            <input value={uid} onChange={(event) => setUid(event.target.value)} />
          </label>
          <label>
            Name
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <button className="primary-button" onClick={() => void createSimulator()}>Create simulator</button>
          <span className="muted-text">{message}</span>
        </div>
      </section>

      <section className="card-grid">
        {devices.map((device) => (
          <article className="asset-card device-card" key={device.device_uid}>
            <div className="preview-toolbar">
              <div>
                <h2>{device.name}</h2>
                <p>{device.device_uid}</p>
              </div>
              <span className={`status-badge ${device.mesh_connected ? "status-good" : "status-warn"}`}>
                {device.mesh_connected ? "mesh" : "pairing"}
              </span>
            </div>
            <dl className="mini-list">
              <div>
                <dt>Battery</dt>
                <dd>{device.battery_percent ?? "N/A"}%</dd>
              </div>
              <div>
                <dt>Firmware</dt>
                <dd>{device.firmware_version ?? "unknown"}</dd>
              </div>
              <div>
                <dt>Last seen</dt>
                <dd>{device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : "Never"}</dd>
              </div>
            </dl>
            <div className="form-stack">
              <label>
                Refresh minutes
                <input
                  type="number"
                  min={10}
                  max={3600}
                  value={device.refresh_interval_minutes}
                  onChange={(event) => void updateDevice(device, { refresh_interval_minutes: Number(event.target.value) })}
                />
              </label>
              {device.refresh_interval_warning && (
                <p className="warning-text">Frequent ePaper refreshes may reduce panel life.</p>
              )}
              <label>
                Source
                <select
                  value={device.selected_source_type}
                  onChange={(event) => void updateDevice(device, { selected_source_type: event.target.value })}
                >
                  <option value="dashboard">Dashboard</option>
                  <option value="photo">Photo</option>
                  <option value="album">Album</option>
                </select>
              </label>
              <button className="secondary-button" onClick={() => void forceManifest(device)}>Prepare frame</button>
            </div>
            <div className="history-list">
              <strong>Recent status</strong>
              {(history[device.device_uid] ?? []).map((item) => (
                <span key={`${item.created_at}-${item.status}`}>
                  {item.status} · {item.battery_percent ?? "N/A"}% · {new Date(item.created_at).toLocaleTimeString()}
                </span>
              ))}
              {!(history[device.device_uid] ?? []).length && <span>No heartbeat history yet.</span>}
            </div>
          </article>
        ))}
        {!devices.length && (
          <section className="empty-state compact">
            <h2>No displays yet</h2>
            <p>Create a simulator or connect a XIAO MG24 display from the pairing flow.</p>
          </section>
        )}
      </section>
    </div>
  );
}
