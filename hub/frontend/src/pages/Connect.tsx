export function Connect() {
  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <h1>Connect inkDaddy</h1>
          <p>Pair a XIAO MG24 display with Matter over Thread and confirm it appears in the hub.</p>
        </div>
      </header>
      <section className="connect-flow">
        <div className="qr-card">
          <div className="qr-mock" aria-label="Matter QR code preview" />
          <div>
            <h2>Display pairing mode</h2>
            <p>Scan the QR code shown on the ePaper display, or enter the manual code and discriminator.</p>
          </div>
        </div>
        <ol className="step-list">
          <li>Confirm a Thread Border Router is online.</li>
          <li>Power the inkDaddy display and wait for the join screen.</li>
          <li>Commission with Matter, then return here to name the display.</li>
          <li>Select a dashboard, photo playlist, and refresh interval.</li>
        </ol>
      </section>
    </div>
  );
}
