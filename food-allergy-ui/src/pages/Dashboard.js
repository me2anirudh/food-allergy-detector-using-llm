import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import NavBar from "../components/NavBar";

export default function Dashboard() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [productName, setProductName] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingAdvice, setLoadingAdvice] = useState(false);
  const [loadingAlternatives, setLoadingAlternatives] = useState(false);
  const [userAllergies, setUserAllergies] = useState([]);
  const [personalizedAdvice, setPersonalizedAdvice] = useState(null);
  const [alternativeList, setAlternativeList] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.getAllergies()
      .then((res) => res.json())
      .then((data) => {
        const arr = (data.allergies || "")
          .split(",")
          .map((s) => s.trim().toLowerCase())
          .filter(Boolean);
        setUserAllergies(arr);
      })
      .catch(() => setUserAllergies([]));
  }, []);

  const onFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setResult(null);
    setProductName("");
    setPersonalizedAdvice(null);
    setAlternativeList([]);
  };

  const runPersonalizedLLMFeatures = async (scanJson, userRisk) => {
    const detected = (userRisk || []).filter(Boolean);

    setLoadingAdvice(true);
    try {
      const adviceRes = await api.getPersonalizedAdvice({
        product_name: productName.trim(),
        detected_allergens: detected,
        ingredients_text: scanJson.ocr_raw_text || "",
      });
      const adviceJson = await adviceRes.json();
      if (adviceJson.success) {
        setPersonalizedAdvice(adviceJson.advice);
      } else {
        setPersonalizedAdvice(null);
      }
    } catch (err) {
      console.error(err);
      setPersonalizedAdvice(null);
    } finally {
      setLoadingAdvice(false);
    }

    if (!detected.length) {
      setAlternativeList([]);
      return;
    }

    setLoadingAlternatives(true);
    try {
      const altRes = await api.getAlternatives({
        product_name: productName.trim(),
        detected_allergens: detected,
      });
      const altJson = await altRes.json();
      if (altJson.success) {
        setAlternativeList(Array.isArray(altJson.alternatives) ? altJson.alternatives : []);
      } else {
        setAlternativeList([]);
      }
    } catch (err) {
      console.error(err);
      setAlternativeList([]);
    } finally {
      setLoadingAlternatives(false);
    }
  };

  const handleScan = async () => {
    if (!selectedFile) {
      alert("Please choose an image first.");
      return;
    }
    if (!productName.trim()) {
      alert("Please enter a product name.");
      return;
    }

    setLoading(true);
    setPersonalizedAdvice(null);
    setAlternativeList([]);

    try {
      const [scanRes, allergiesRes] = await Promise.all([api.scanImage(selectedFile), api.getAllergies()]);

      let scanJson = {};
      let allergiesJson = {};
      try {
        scanJson = await scanRes.json();
      } catch {
        throw new Error(`Scan request failed with status ${scanRes.status}`);
      }
      try {
        allergiesJson = await allergiesRes.json();
      } catch {
        allergiesJson = {};
      }

      if (!scanRes.ok) {
        throw new Error(scanJson.error || scanJson.message || "Scan request failed.");
      }

      if (!allergiesRes.ok) {
        console.warn("Could not fetch allergies; fallback matching may be limited.");
      }
      const saved = (allergiesJson.allergies || "")
        .split(",")
        .map((s) => s.trim().toLowerCase())
        .filter(Boolean);

      let userRisk = (scanJson.user_specific_risk || []).filter(Boolean);
      if (!userRisk.length && saved.length) {
        const combined = (scanJson.combined_allergens || []).map((s) => s.toLowerCase());
        userRisk = saved.filter((a) => combined.includes(a));
      }

      const finalResult = { ...scanJson, user_specific_risk: userRisk };
      setResult(finalResult);

      const isUnsafe = userRisk.length > 0;
      const saveData = {
        product_name: productName.trim(),
        ingredients: scanJson.ocr_raw_text || "",
        result: isUnsafe ? "UNSAFE" : "SAFE",
        allergens_found: userRisk.join(", "),
      };

      const saveRes = await api.saveScan(saveData);
      const saveJson = await saveRes.json();
      if (!saveJson.success) {
        alert(`Scan completed, but failed to save to history: ${saveJson.message}`);
      }

      await runPersonalizedLLMFeatures(scanJson, userRisk);
    } catch (err) {
      console.error(err);
      alert(`Scan failed: ${err.message || "Unknown error"}`);
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

  const badgeClass = result ? `badge ${verdict.status.toLowerCase()} ${verdict.status === "UNSAFE" ? "pulse" : ""}` : "badge";
  const ariaLive = result ? (verdict.status === "UNSAFE" ? "assertive" : "polite") : "polite";

  return (
    <div className="page">
      <div style={{ width: "100%", maxWidth: 760 }}>
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
                <p style={{ color: "#666", marginBottom: 8 }}>No allergies set - go to Edit Allergies to add</p>
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
                  <div style={{ marginTop: 8 }}>
                    <label htmlFor="productName">Product Name:</label>
                    <input
                      id="productName"
                      type="text"
                      value={productName}
                      onChange={(e) => setProductName(e.target.value)}
                      placeholder="Enter a unique name for this product"
                      style={{ width: "100%", marginTop: 4, padding: 8, border: "1px solid #ccc", borderRadius: 4 }}
                    />
                  </div>
                </div>
              )}

              <div style={{ marginTop: 8, display: "flex", gap: 12, flexWrap: "wrap" }}>
                <button onClick={handleScan} disabled={!selectedFile || loading} style={{ minWidth: 140 }}>
                  {loading ? "Scanning..." : "Scan"}
                </button>
                <button onClick={() => navigate("/allergies")} className="secondary" style={{ minWidth: 140 }}>
                  Edit Allergies
                </button>
                <button onClick={() => navigate("/emergency")} className="secondary" style={{ minWidth: 140 }}>
                  Emergency Help
                </button>
              </div>

              {result && (
                <div className="result fade-in" role="status" aria-live={ariaLive} style={{ marginTop: 12 }}>
                  <div className={badgeClass}>{verdict.status}</div>
                  <p style={{ marginTop: 8, marginBottom: 0 }}>{verdict.msg}</p>

                  {loadingAdvice && (
                    <div style={{ marginTop: 12, padding: 12, background: "#f0f8ff", borderRadius: 6, borderLeft: "4px solid #1b7f4b" }}>
                      <p style={{ margin: 0, color: "#555", fontStyle: "italic" }}>Generating personalized explanation...</p>
                    </div>
                  )}

                  {personalizedAdvice && !loadingAdvice && (
                    <div style={{ marginTop: 12, padding: 12, background: "#f0f8ff", borderRadius: 6, borderLeft: "4px solid #1b7f4b" }}>
                      <p style={{ margin: "0 0 8px 0", color: "#1b7f4b", fontWeight: 700 }}>AI Safety Explanation</p>
                      <p style={{ margin: "0 0 8px 0" }}><strong>Summary:</strong> {personalizedAdvice.verdict_summary}</p>
                      <p style={{ margin: "0 0 8px 0" }}><strong>Risk:</strong> {personalizedAdvice.risk_explanation}</p>
                      {personalizedAdvice.hidden_ingredient_watchouts?.length > 0 && (
                        <p style={{ margin: "0 0 8px 0" }}>
                          <strong>Watch outs:</strong> {personalizedAdvice.hidden_ingredient_watchouts.join(", ")}
                        </p>
                      )}
                      <p style={{ margin: "0 0 8px 0" }}><strong>Next step:</strong> {personalizedAdvice.safer_next_step}</p>
                      <p style={{ margin: 0, fontSize: 12, color: "#666" }}>{personalizedAdvice.disclaimer}</p>
                    </div>
                  )}

                  {loadingAlternatives && (
                    <div style={{ marginTop: 12, color: "#555", fontStyle: "italic" }}>Finding safer alternatives...</div>
                  )}

                  {!loadingAlternatives && alternativeList.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <p style={{ margin: "0 0 8px 0", fontWeight: 700, color: "#1b7f4b" }}>Safer alternatives</p>
                      {alternativeList.map((item, idx) => (
                        <div key={`${item.alternative_name}-${idx}`} style={{ marginBottom: 8, padding: 10, background: "#f8fbff", border: "1px solid #d8e8ff", borderRadius: 6 }}>
                          <p style={{ margin: "0 0 6px 0", fontWeight: 700 }}>{item.alternative_name}</p>
                          <p style={{ margin: "0 0 4px 0" }}>{item.why_safer}</p>
                          <p style={{ margin: 0, fontSize: 13, color: "#555" }}><strong>Caution:</strong> {item.caution_note}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
