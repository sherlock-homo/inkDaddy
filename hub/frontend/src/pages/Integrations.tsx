import { useEffect, useState } from "react";
import { apiJson, statusTone } from "../lib/api";
import type { IntegrationRecord } from "../lib/types";

export function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<IntegrationRecord[]>([]);
  const [message, setMessage] = useState("Loading integrations");

  useEffect(() => {
    apiJson<{ integrations: IntegrationRecord[] }>("/api/integrations")
      .then((payload) => {
        setIntegrations(payload.integrations);
        setMessage("Ready");
      })
      .catch((error: Error) => setMessage(error.message));
  }, []);

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>Integrations</h1>
          <p>Manage local data sources and device-facing services that feed inkDaddy displays.</p>
        </div>
      </header>

      <section className="card-grid three">
        {integrations.map((integration) => (
          <article className="asset-card integration-card" key={integration.id}>
            <div className="preview-toolbar">
              <div>
                <h2>{integration.name}</h2>
                <p>{integration.configured ? "Configured" : "Setup needed"}</p>
              </div>
              <span className={`status-badge ${statusTone(integration.status)}`}>{integration.status}</span>
            </div>
            <dl className="mini-list">
              <div>
                <dt>Enabled</dt>
                <dd>{integration.enabled ? "Yes" : "No"}</dd>
              </div>
              <div>
                <dt>Entities</dt>
                <dd>{integration.entity_count ?? "N/A"}</dd>
              </div>
              <div>
                <dt>Devices</dt>
                <dd>{integration.device_count ?? "N/A"}</dd>
              </div>
            </dl>
            <a className="secondary-link" href={integration.manage_url}>Manage</a>
          </article>
        ))}
      </section>
      <p className="muted-text">{message}</p>
    </div>
  );
}
