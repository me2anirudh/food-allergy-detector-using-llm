import { useEffect, useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";

export default function EditAllergies() {
  const [allergies, setAllergies] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const fetchAllergies = () => {
    api.getAllergies()
      .then(res => res.json())
      .then(data => setAllergies(data.allergies || ""))
      .catch(() => setAllergies(""));
  };

  useEffect(() => {
    fetchAllergies();
  }, []);

  const save = async (payload) => {
    setLoading(true);
    try {
      const res = await api.saveAllergies(payload ?? allergies);
      const data = await res.json();
      if (res.ok) {
        setStatusMsg("Saved");
        fetchAllergies();
      } else {
        setStatusMsg(data.message || "Save failed");
      }
    } catch (err) {
      console.error(err);
      setStatusMsg("Save failed");
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(""), 2500);
    }
  };

  const clearAllergies = () => {
    // eslint-disable-next-line no-restricted-globals
    if (!window.confirm("Clear all allergies?")) return;
    setAllergies("");
    save("");
  };

  return (
    <div className="page">
      <div className="tab-shell fade-in">
        <NavBar />
        <div className="card tab-card">
          <div className="card-header">
            <div>
              <h2>Edit Allergies</h2>
              <div className="brand-sub">List allergies separated by commas (e.g. wheat, milk)</div>
            </div>
          </div>

          <input
            value={allergies}
            onChange={e => setAllergies(e.target.value)}
            placeholder="milk, egg, peanut"
          />

          <button onClick={() => save(allergies)} disabled={loading}>
            {loading ? "Saving..." : "Save"}
          </button>

          <button className="secondary" onClick={clearAllergies} disabled={loading}>
            Clear Allergies
          </button>

          {statusMsg && <p className="statusMsg fade-in" style={{ color: "#1b7f4b", fontWeight: 600, marginTop: 12 }}>{statusMsg}</p>}

          <button className="secondary" onClick={() => navigate("/dashboard")}>Back to Dashboard</button>
        </div>
      </div>
    </div>
  );
}



