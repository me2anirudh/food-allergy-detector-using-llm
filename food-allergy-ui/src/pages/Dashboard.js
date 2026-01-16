import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import NavBar from "../components/NavBar";

export default function Dashboard() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [userAllergies, setUserAllergies] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    // fetch saved allergies for client-side fallback matching
    api.getAllergies()
      .then(res => res.json())
      .then(data => {
        const arr = (data.allergies || "").split(",").map(s => s.trim().toLowerCase()).filter(Boolean);
        setUserAllergies(arr);
      })
      .catch(() => setUserAllergies([]));
  }, []);

  const onFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setResult(null);
  };

  const handleScan = async () => {
    if (!selectedFile) {
      alert("Please choose an image first.");
      return;
    }

    setLoading(true);
    try {
      const [scanRes, allergiesRes] = await Promise.all([
        api.scanImage(selectedFile),
        api.getAllergies()
      ]);

      const scanJson = await scanRes.json();
      const allergiesJson = await allergiesRes.json();
      const saved = (allergiesJson.allergies || "").split(",").map(s => s.trim().toLowerCase()).filter(Boolean);

      // server may return user_specific_risk if session was recognized
      let userRisk = (scanJson.user_specific_risk || []).filter(Boolean);

      // Fallback: compute intersection client-side if server didn't provide personalization
      if (!userRisk.length && saved.length) {
        const combined = (scanJson.combined_allergens || []).map(s => s.toLowerCase());
        userRisk = saved.filter(a => combined.includes(a));
      }

      setResult({ ...scanJson, user_specific_risk: userRisk });
    } catch (err) {
      console.error(err);
      alert("Scan failed. See console for details.");
    } finally {
      setLoading(false);
    }
  };

  const verdict =
    result && result.user_specific_risk && result.user_specific_risk.length > 0
      ? {
          status: "UNSAFE",
          msg: `Contains ${result.user_specific_risk.join(", ")}. Consume at your own risk.`,
        }
      : { status: "SAFE", msg: "Can be consumed safely." };

  const badgeClass = result ? `badge ${verdict.status.toLowerCase()} ${verdict.status === 'UNSAFE' ? 'pulse' : ''}` : 'badge';
  const ariaLive = result ? (verdict.status === 'UNSAFE' ? 'assertive' : 'polite') : 'polite';

  return (
    <div className="page">
      <div style={{ width: "100%", maxWidth: 640 }}>
        <NavBar />
        <div className="card">
          <div className="card-header">
            <div>
              <h2>Scan Product</h2>
              <div className="brand-sub">Upload product image to check against your saved allergies</div>
            </div>
          </div>

          <div className="card-body stacked">
            <div className="card-left">
              {userAllergies.length > 0 ? (
                <p style={{ color: "#1b7f4b", marginBottom: 8, fontWeight: 600 }}>Your allergies: {userAllergies.join(", ")}</p>
              ) : (
                <p style={{ color: "#666", marginBottom: 8 }}>No allergies set — go to Edit Allergies to add</p>
              )}

              <div style={{ marginBottom: 12 }}>
                <input type="file" accept="image/*" onChange={onFileChange} />
              </div>

              {selectedFile && (
                <div style={{ textAlign: "left", marginBottom: 12 }}>
                  <div><strong>Selected:</strong> {selectedFile.name}</div>
                  <div style={{ marginTop: 8 }}>
                    <img className="preview" src={URL.createObjectURL(selectedFile)} alt="preview" />
                  </div>
                </div>
              )}

              <div style={{ marginTop: 8, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button onClick={handleScan} disabled={!selectedFile || loading} style={{ minWidth: 140 }}>
                  {loading ? "Scanning..." : "Scan"}
                </button>

                <button onClick={() => navigate("/allergies")} className="secondary" style={{ minWidth: 140 }}>
                  Edit Allergies
                </button>
              </div>

              {result && (
                <div className="result fade-in" role="status" aria-live={ariaLive} style={{ marginTop: 12 }}>
                  <div className={badgeClass}>{verdict.status}</div>
                  <p style={{ marginTop: 8, marginBottom: 0 }}>{verdict.msg}</p>
                </div>
              )}
            </div>
          </div>
        </div>
    </div>
  </div>
  );
}
