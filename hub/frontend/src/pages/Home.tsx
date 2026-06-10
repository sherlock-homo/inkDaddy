import { EpaperPreview } from "../components/EpaperPreview";
import { StatusBadge } from "../components/StatusBadge";
import type { DisplayStatus } from "../lib/types";

export function Home({ display, onConnect }: { display: DisplayStatus; onConnect: () => void }) {
  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>Home</h1>
          <p>Local display control, Home Assistant state, and ePaper frame publishing.</p>
        </div>
        {!display.meshConnected && (
          <button className="primary-button" onClick={onConnect}>
            Connect inkDaddy
          </button>
        )}
      </header>

      {!display.meshConnected && (
        <section className="callout">
          <div>
            <h2>Matter pairing screen is active</h2>
            <p>
              Until this display joins the Thread mesh, inkDaddy alternates the Matter QR/manual
              pairing screen with queued content. If no content exists, it shows only pairing steps.
            </p>
          </div>
          <StatusBadge tone="warn">Unjoined</StatusBadge>
        </section>
      )}

      <section className="metric-grid">
        <Metric label="Selected display" value={display.name} detail="XIAO MG24 target" />
        <Metric label="Last refresh" value={display.lastRefresh} detail="No errors reported" />
        <Metric label="Battery" value={`${display.batteryPercent}%`} detail="Safe for OTA" />
        <Metric label="Next wake" value={display.nextWake} detail="30 min interval" />
      </section>

      <div className="content-layout">
        <EpaperPreview />
        <aside className="side-stack">
          <Panel title="Active mode" value={display.activeMode} tone="good" />
          <Panel title="Home Assistant" value="Token not configured" tone="warn" />
          <Panel title="Updates" value="Release source not configured" tone="neutral" />
          <Panel title="Thread diagnostics" value="Border router check pending" tone="warn" />
        </aside>
      </div>
    </div>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function Panel({ title, value, tone }: { title: string; value: string; tone: "good" | "warn" | "neutral" }) {
  return (
    <section className="info-panel">
      <div>
        <h2>{title}</h2>
        <p>{value}</p>
      </div>
      <StatusBadge tone={tone}>{tone === "good" ? "Ready" : tone === "warn" ? "Needs setup" : "Idle"}</StatusBadge>
    </section>
  );
}
