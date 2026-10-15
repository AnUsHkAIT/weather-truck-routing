import { RISK_COLORS } from "./MapView";

const fmtDur = (s) => `${Math.floor(s / 3600)}h ${Math.round((s % 3600) / 60)}m`;
const fmtTime = (iso) =>
  new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

export default function Sidebar({ form, setForm, onSubmit, loading, error, result, selected, setSelected }) {
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const route = result?.routes.find((r) => r.id === selected);

  return (
    <div className="sidebar">
      <h1>Weather-Aware Truck Routing</h1>
      <form onSubmit={onSubmit}>
        <label>Origin</label>
        <input value={form.origin} onChange={set("origin")} required />
        <label>Destination</label>
        <input value={form.destination} onChange={set("destination")} required />
        <label>Departure (your local time)</label>
        <input type="datetime-local" value={form.departure} onChange={set("departure")} required />
        <label>Load weight (lb)</label>
        <input type="number" min="0" max="150000" value={form.load_lb} onChange={set("load_lb")} required />
        <button className="go" disabled={loading}>{loading ? "Planning (5-20 s)..." : "Find safest route"}</button>
      </form>

      {error && <div className="error">{error}</div>}
      {loading && [1, 2, 3].map((i) => <div key={i} className="skeleton" />)}

      {!loading && result && result.routes.map((r) => (
        <div key={r.id} className={`card ${r.id === selected ? "sel" : ""}`} onClick={() => setSelected(r.id)}>
          <h3>
            {r.name}
            {r.recommended && <span className="badge">Recommended</span>}
            {r.no_travel_miles > 0 && <span className="badge warn">No Travel</span>}
          </h3>
          <div className="stats">
            <span>Time: {fmtDur(r.duration_s)}</span>
            <span>Distance: {r.miles} mi</span>
            <span>Severe miles: {Math.round(r.severe_miles)}</span>
            <span>High miles: {Math.round(r.high_miles)}</span>
            <span>Avg risk: {r.avg_risk.toFixed(2)} / 4</span>
            <span>Arrive: {fmtTime(r.arrival)}</span>
          </div>
          {r.recommended && <div className="why">{r.explanation}</div>}
        </div>
      ))}

      {!loading && route && (
        <>
          <h3 style={{ marginBottom: 0 }}>Checkpoints: {route.name}</h3>
          <table>
            <thead>
              <tr><th>Mi</th><th>ETA</th><th>Wind</th><th>Rain</th><th>Snow</th><th>Risk</th></tr>
            </thead>
            <tbody>
              {route.checkpoints.map((c) => (
                <tr key={c.mile} title={c.reasons.join("; ")}>
                  <td>{Math.round(c.mile)}</td>
                  <td>{fmtTime(c.eta)}</td>
                  <td>{c.wind_mph}</td>
                  <td>{c.rain_in_hr}</td>
                  <td>{c.snow_in_hr}</td>
                  <td><span className="dot" style={{ background: RISK_COLORS[c.risk] }} />{c.risk_label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}