import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export const RISK_COLORS = ["#2e9e4f", "#e6c200", "#f08a00", "#d62828", "#111111"];
const LEVELS = ["Low", "Moderate", "High", "Severe", "No Travel"];
const ROUTE_COLORS = ["#2563eb", "#9333ea", "#0d9488"];

function FitBounds({ result }) {
  const map = useMap();
  useEffect(() => {
    if (!result) return;
    const pts = result.routes.flatMap((r) => r.geometry);
    if (pts.length) map.fitBounds(L.latLngBounds(pts), { padding: [40, 40] });
  }, [result, map]);
  return null;
}

function HeatLayer({ heatmap, hour }) {
  const map = useMap();
  const layerRef = useRef(null);

  // risk level 0..4 -> intensity 0.2..1.0, so even "Low" shows as a green glow
  const dataAt = (h) => heatmap.points.map((p) => [p.lat, p.lon, (p.levels[h] + 1) / 5]);

  // create the layer once per result
  useEffect(() => {
    let cancelled = false;
    window.L = L; // leaflet.heat expects a global L
    import("leaflet.heat").then(() => {
      if (cancelled) return;
      layerRef.current = L.heatLayer(dataAt(0), {
        radius: 40,
        blur: 30,
        max: 1,
        minOpacity: 0.35,
        gradient: { 0.2: "#2e9e4f", 0.4: "#e6c200", 0.6: "#f08a00", 0.8: "#d62828", 1: "#111111" },
      }).addTo(map);
    });
    return () => {
      cancelled = true;
      if (layerRef.current) map.removeLayer(layerRef.current);
      layerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [heatmap, map]);

  // the slider only swaps the data: no refetch, no re-create
  useEffect(() => {
    if (layerRef.current) layerRef.current.setLatLngs(dataAt(hour));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hour]);

  return null;
}

export default function MapView({ result, selected, setSelected, hour, setHour }) {
  const ordered = result ? [...result.routes].sort((a, b) => (a.id === selected) - (b.id === selected)) : [];
  const clock = result
    ? new Date(new Date(result.heatmap.start).getTime() + hour * 3600000).toLocaleString([], {
        weekday: "short", hour: "2-digit", minute: "2-digit",
      })
    : "";

  return (
    <>
      <MapContainer center={[39.5, -98.35]} zoom={4} preferCanvas>
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {result && <FitBounds result={result} />}
        {result && <HeatLayer heatmap={result.heatmap} hour={hour} />}

        {ordered.map((r) => (
          <Polyline
            key={`line-${r.id}`}
            positions={r.geometry}
            pathOptions={{
              color: ROUTE_COLORS[r.id % 3],
              weight: r.id === selected ? 7 : 4,
              opacity: r.id === selected ? 0.95 : 0.45,
            }}
            eventHandlers={{ click: () => setSelected(r.id) }}
          />
        ))}

        {ordered.flatMap((r) =>
          r.checkpoints.map((c) => (
            <CircleMarker
              key={`${r.id}-${c.mile}`}
              center={[c.lat, c.lon]}
              radius={r.id === selected ? 6 : 3}
              pathOptions={{ color: "#fff", weight: 1, fillColor: RISK_COLORS[c.risk], fillOpacity: 1 }}
            >
              <Popup>
                <b>{r.name}</b>, mile {Math.round(c.mile)}<br />
                ETA: {new Date(c.eta).toLocaleString()}<br />
                Wind {c.wind_mph} mph, rain {c.rain_in_hr} in/hr, snow {c.snow_in_hr} in/hr<br />
                <b>Risk: {c.risk_label}</b>
                {c.reasons.map((x) => <div key={x}>{x}</div>)}
              </Popup>
            </CircleMarker>
          ))
        )}
      </MapContainer>

      {result && (
        <div className="slider">
          <b>Weather forecast heatmap:</b> +{hour} h ({clock})
          <input type="range" min="0" max={result.heatmap.hours} value={hour}
                 onChange={(e) => setHour(Number(e.target.value))} />
          <div className="legend">
            {LEVELS.map((l, i) => (
              <span key={l}><span className="dot" style={{ background: RISK_COLORS[i] }} />{l}</span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}