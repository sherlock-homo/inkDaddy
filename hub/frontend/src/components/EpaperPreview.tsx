export function EpaperPreview() {
  const tiles = [
    ["72F", "Living Room"],
    ["Weather", "Light rain"],
    ["Door", "Closed"],
    ["Battery", "87%"],
    ["Energy", "4.2 kWh"],
    ["Agenda", "3 events"],
    ["Photo", "Shuffle"],
    ["Wake", "18 min"]
  ];
  return (
    <section className="preview-panel" aria-label="Current ePaper preview">
      <div className="preview-toolbar">
        <div>
          <h2>Current preview</h2>
          <p>800 x 480 · 6-color packed raw</p>
        </div>
        <button className="icon-button" aria-label="Refresh preview">
          ↻
        </button>
      </div>
      <div className="epaper-frame">
        <div className="epaper-grid">
          {tiles.map(([title, value]) => (
            <div className="epaper-tile" key={title}>
              <strong>{title}</strong>
              <span>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
