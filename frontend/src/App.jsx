import { useState } from "react";
import Sidebar from "./Sidebar";
import MapView from "./MapView";
import "./index.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function defaultDeparture() {
  const d = new Date(Date.now() + 3600000);
  d.setMinutes(0, 0, 0);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:00`;
}

export default function App() {
  const [form, setForm] = useState({
    origin: "Denver, CO",
    destination: "Chicago, IL",
    departure: defaultDeparture(),
    load_lb: 45000,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState(0);
  const [hour, setHour] = useState(0);

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/plan/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin: form.origin,
          destination: form.destination,
          departure: new Date(form.departure).toISOString(),
          load_lb: Number(form.load_lb),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(
          data.error ||
            Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(" ")}`).join(" | ")
        );
      }
      setResult(data);
      setSelected(data.recommended_id);
      setHour(0);
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <Sidebar
        form={form} setForm={setForm} onSubmit={submit}
        loading={loading} error={error}
        result={result} selected={selected} setSelected={setSelected}
      />
      <div className="map-wrap">
        <MapView
          result={result} selected={selected} setSelected={setSelected}
          hour={hour} setHour={setHour}
        />
      </div>
    </div>
  );
}