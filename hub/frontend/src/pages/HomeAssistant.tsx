import { useEffect, useMemo, useState } from "react";
import { apiJson } from "../lib/api";
import type { HAConfig, HAEntity } from "../lib/types";

export function HomeAssistantPage() {
  const [config, setConfig] = useState<HAConfig | null>(null);
  const [entities, setEntities] = useState<HAEntity[]>([]);
  const [baseUrl, setBaseUrl] = useState("http://homeassistant.local:8123");
  const [token, setToken] = useState("");
  const [search, setSearch] = useState("");
  const [domain, setDomain] = useState("");
  const [message, setMessage] = useState("Ready");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const [configPayload, entityPayload] = await Promise.all([
      apiJson<HAConfig>("/api/home-assistant/config"),
      apiJson<{ entities: HAEntity[] }>("/api/home-assistant/entities?limit=100")
    ]);
    setConfig(configPayload);
    setBaseUrl(configPayload.base_url);
    setEntities(entityPayload.entities);
  };

  useEffect(() => {
    load().catch((error: Error) => setMessage(error.message));
  }, []);

  const domains = useMemo(() => Array.from(new Set(entities.map((entity) => entity.domain))).sort(), [entities]);
  const filtered = entities.filter((entity) => {
    const haystack = `${entity.entity_id} ${entity.name ?? ""} ${entity.state ?? ""}`.toLowerCase();
    return (!domain || entity.domain === domain) && (!search || haystack.includes(search.toLowerCase()));
  });

  const save = async () => {
    setBusy(true);
    try {
      const payload = await apiJson<HAConfig>("/api/home-assistant/config", {
        method: "PUT",
        body: JSON.stringify({ base_url: baseUrl, token, enabled: true, validate: Boolean(token) })
      });
      setConfig(payload);
      setToken("");
      setMessage("Home Assistant configuration saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to save Home Assistant config.");
    } finally {
      setBusy(false);
    }
  };

  const refresh = async () => {
    setBusy(true);
    try {
      const payload = await apiJson<{ entities: HAEntity[]; error?: string | null }>("/api/home-assistant/entities?refresh=true&limit=500");
      setEntities(payload.entities);
      setMessage(payload.error ?? `Cached ${payload.entities.length} entities.`);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to refresh entities.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>Home Assistant</h1>
          <p>Connect with a long-lived token, validate it locally, and cache entity metadata for dashboard widgets.</p>
        </div>
        <span className={`status-badge ${config?.configured ? "status-good" : "status-warn"}`}>
          {config?.configured ? "configured" : "not configured"}
        </span>
      </header>

      <section className="settings-grid">
        <div className="workflow-panel">
          <div className="form-stack">
            <label>
              Home Assistant URL
              <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
            </label>
            <label>
              Long-lived access token
              <textarea
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder={config?.token_preview ? `Stored token ${config.token_preview}` : "Paste token"}
                rows={4}
              />
            </label>
            <div className="button-row">
              <a className="secondary-link" href={config?.token_page_url ?? `${baseUrl}/profile`} target="_blank" rel="noreferrer">
                Open token page
              </a>
              <button className="primary-button" disabled={busy} onClick={() => void save()}>
                {busy ? "Working..." : "Save and validate"}
              </button>
              <button className="secondary-button" disabled={busy || !config?.configured} onClick={() => void refresh()}>
                Refresh entities
              </button>
            </div>
            <p className="muted-text">{message}</p>
          </div>
        </div>

        <div className="info-panel vertical">
          <h2>Cache</h2>
          <div className="row-item">
            <span>Entities</span>
            <strong>{config?.entity_count ?? entities.length}</strong>
          </div>
          <div className="row-item">
            <span>Last validated</span>
            <strong>{config?.last_validated_at ? new Date(config.last_validated_at).toLocaleString() : "Never"}</strong>
          </div>
        </div>
      </section>

      <section className="workflow-panel">
        <div className="form-row">
          <label>
            Search
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="temperature, door, light..." />
          </label>
          <label>
            Domain
            <select value={domain} onChange={(event) => setDomain(event.target.value)}>
              <option value="">All</option>
              {domains.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="table-panel">
        {filtered.map((entity) => (
          <div className="table-row" key={entity.entity_id}>
            <div>
              <strong>{entity.name ?? entity.entity_id}</strong>
              <span>{entity.entity_id}</span>
            </div>
            <span className="status-badge status-neutral">{entity.domain}</span>
            <strong>{entity.state ?? "unknown"}</strong>
          </div>
        ))}
        {!filtered.length && (
          <section className="empty-state compact">
            <h2>No cached entities</h2>
            <p>Save a token and refresh entities to bind dashboards to Home Assistant.</p>
          </section>
        )}
      </section>
    </div>
  );
}
