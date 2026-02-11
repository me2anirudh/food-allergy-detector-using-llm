import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import NavBar from "../components/NavBar";

export default function History() {
  const [history, setHistory] = useState([]);
  const [filteredHistory, setFilteredHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    // Filter history based on search term
    const filtered = history.filter(item =>
      item.product_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredHistory(filtered);
  }, [history, searchTerm]);

  const fetchHistory = async () => {
    try {
      const res = await api.getHistory();
      const data = await res.json();
      if (data.success) {
        setHistory(data.history);
      } else {
        alert("Failed to load history: " + data.message);
      }
    } catch (err) {
      console.error(err);
      alert("Error loading history.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <NavBar />
      <div className="container fade-in">
        <h1>Scan History</h1>
        <p>View all your scanned products and their safety status.</p>

        {/* Navigation Links */}
        <div className="tab-links">
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/allergies")}>Edit Allergies</button>
          <button onClick={() => navigate("/education")}>Education</button>
          <button className="active">History</button>
        </div>

        {/* Search Input */}
        <div className="search-container">
          <input
            type="text"
            placeholder="Search products by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        {loading ? (
          <p>Loading history...</p>
        ) : filteredHistory.length === 0 ? (
          <p>{searchTerm ? "No products match your search." : "No scans yet. Start by scanning a product!"}</p>
        ) : (
          <div className="history-grid">
            {filteredHistory.map((item, index) => (
              <div key={index} className="history-card">
                <h3>{item.product_name}</h3>
                <p>
                  <span className={`result-badge ${item.result.toLowerCase()}`}>
                    {item.result}
                  </span>
                </p>
                {item.allergens_found && (
                  <p><strong>Allergens Found:</strong> {item.allergens_found}</p>
                )}
                <p className="timestamp">
                  Scanned on: {new Date(item.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}