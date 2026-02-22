import { useState } from "react";
import NavBar from "../components/NavBar";
import api from "../api";

export default function EmergencyHelp() {
  const [suspectedAllergen, setSuspectedAllergen] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [hasEpinephrine, setHasEpinephrine] = useState("yes");
  const [ageGroup, setAgeGroup] = useState("adult");
  const [loading, setLoading] = useState(false);
  const [guidance, setGuidance] = useState(null);

  const submit = async () => {
    if (!symptoms.trim()) {
      alert("Please enter symptoms.");
      return;
    }

    setLoading(true);
    setGuidance(null);
    try {
      const res = await api.getEmergencyGuidance({
        suspected_allergen: suspectedAllergen.trim(),
        symptoms: symptoms.trim(),
        has_epinephrine: hasEpinephrine,
        age_group: ageGroup,
      });
      const json = await res.json();
      if (!json.success) {
        alert(json.message || "Could not get guidance.");
      } else {
        setGuidance(json.guidance);
      }
    } catch (err) {
      console.error(err);
      alert("Error while getting emergency guidance.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div style={{ width: "100%", maxWidth: 760 }}>
        <NavBar />
        <div className="card">
          <div className="card-header">
            <div>
              <h2>Emergency Help</h2>
              <div className="brand-sub">Use this for immediate action guidance while contacting medical professionals.</div>
            </div>
          </div>
          <div className="card-body stacked">
            <p style={{ color: "#a10000", fontWeight: 700, marginTop: 0 }}>
              Severe symptoms need emergency services immediately. This tool is not a replacement for medical care.
            </p>

            <label>Suspected Allergen</label>
            <input
              type="text"
              value={suspectedAllergen}
              onChange={(e) => setSuspectedAllergen(e.target.value)}
              placeholder="e.g., milk"
              style={{ marginBottom: 10, padding: 10, border: "1px solid #ccc", borderRadius: 6 }}
            />

            <label>Symptoms</label>
            <textarea
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              placeholder="e.g., swelling lips, breathing difficulty, hives"
              rows={4}
              style={{ marginBottom: 10, padding: 10, border: "1px solid #ccc", borderRadius: 6 }}
            />

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 10 }}>
              <div>
                <label>Epinephrine available</label>
                <select value={hasEpinephrine} onChange={(e) => setHasEpinephrine(e.target.value)} style={{ marginLeft: 8 }}>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div>
                <label>Age Group</label>
                <select value={ageGroup} onChange={(e) => setAgeGroup(e.target.value)} style={{ marginLeft: 8 }}>
                  <option value="child">Child</option>
                  <option value="adult">Adult</option>
                  <option value="older_adult">Older Adult</option>
                </select>
              </div>
            </div>

            <button onClick={submit} disabled={loading}>{loading ? "Generating..." : "Get Emergency Guidance"}</button>

            {guidance && (
              <div style={{ marginTop: 16, padding: 12, border: "1px solid #f3c2c2", borderRadius: 8, background: "#fff8f8" }}>
                <p style={{ marginTop: 0 }}><strong>Severity:</strong> {guidance.severity_level}</p>
                <p><strong>Immediate Actions:</strong></p>
                <ol>
                  {(guidance.immediate_actions || []).map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
                <p><strong>When to seek emergency care:</strong> {guidance.when_to_seek_emergency}</p>
                <p><strong>Follow up:</strong></p>
                <ol>
                  {(guidance.follow_up_actions || []).map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
                <p style={{ color: "#666", marginBottom: 0 }}>{guidance.disclaimer}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
