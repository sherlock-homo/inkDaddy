export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers =
    init?.body instanceof FormData
      ? init.headers
      : { "Content-Type": "application/json", ...(init?.headers as Record<string, string> | undefined) };
  const response = await fetch(path, {
    headers,
    ...init
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export function statusTone(status: string): "status-good" | "status-warn" | "status-danger" | "status-neutral" {
  if (["ready", "connected", "current", "ok"].includes(status)) {
    return "status-good";
  }
  if (["not_configured", "no_devices", "diagnostics_required", "no_firmware_asset"].includes(status)) {
    return "status-warn";
  }
  if (["error", "failed", "offline"].includes(status)) {
    return "status-danger";
  }
  return "status-neutral";
}
