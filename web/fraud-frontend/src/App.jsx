import { useState } from "react";

const N_FEATURES = 30;

export default function App() {
  const [features, setFeatures] = useState(Array(N_FEATURES).fill(0));
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const updateValue = (idx, val) => {
    const next = [...features];
    next[idx] = val === "" ? "" : Number(val);
    setFeatures(next);
  };

  const pasteCSV = () => {
    const line = prompt("Paste a comma-separated line of 30 numbers:");
    if (!line) return;
    const nums = line.split(",").map(s => Number(s.trim()));
    if (nums.length !== N_FEATURES || nums.some(n => Number.isNaN(n))) {
      alert("Expected exactly 30 numeric values.");
      return;
    }
    setFeatures(nums);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);

    if (features.length !== N_FEATURES || features.some(v => v === "" || Number.isNaN(Number(v)))) {
      setError("Please fill all 30 numeric values.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE}/score`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": import.meta.env.VITE_API_KEY
        },
        body: JSON.stringify({ features })
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 980, margin: "40px auto", fontFamily: "ui-sans-serif, system-ui" }}>
      <h1 style={{ marginBottom: 8 }}>Credit Card Fraud Scorer</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Backend: FastAPI on ECS. Enter 30 features (Time, V1..V28, Amount).
      </p>

      <button onClick={pasteCSV} style={{ marginBottom: 12 }}>
        Paste 30 values (CSV)
      </button>

      <form onSubmit={submit}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, minmax(150px, 1fr))",
            gap: 10,
            marginBottom: 12
          }}
        >
          {Array.from({ length: N_FEATURES }).map((_, i) => (
            <div key={i} style={{ display: "flex", flexDirection: "column" }}>
              <label style={{ fontSize: 12, color: "#444" }}>
                {i === 0 ? "Time" : i === N_FEATURES - 1 ? "Amount" : `V${i}`}
              </label>
              <input
                type="number"
                step="any"
                value={features[i]}
                onChange={(e) => updateValue(i, e.target.value)}
                style={{ padding: 8, borderRadius: 6, border: "1px solid #ccc" }}
              />
            </div>
          ))}
        </div>

        <button disabled={loading} style={{ padding: "10px 16px" }}>
          {loading ? "Scoring..." : "Score"}
        </button>
      </form>

      {error && (
        <p style={{ color: "crimson", marginTop: 16 }}>
          {error}
        </p>
      )}

      {result && (
        <div style={{ marginTop: 16, padding: 12, border: "1px solid #ddd", borderRadius: 8 }}>
          <div><strong>probability</strong>: {result.probability?.toFixed(6)}</div>
          <div><strong>is_fraud</strong>: {String(result.is_fraud)}</div>
          <div><strong>threshold</strong>: {result.threshold}</div>
        </div>
      )}
    </div>
  );
}
