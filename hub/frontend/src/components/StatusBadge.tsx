type Tone = "good" | "warn" | "danger" | "neutral";

export function StatusBadge({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  return <span className={`status-badge status-${tone}`}>{children}</span>;
}
