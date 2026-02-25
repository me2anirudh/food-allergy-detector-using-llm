import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import logo from "../assets/allershield_logo.png";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async () => {
    setLoading(true);
    try {
      const res = await api.login({ username, password });
      const data = await res.json();

      if (res.ok && data.success) {
        navigate("/dashboard");
      } else {
        alert(data.message || "Invalid username or password");
      }
    } catch (err) {
      console.error(err);
      alert("Server error. Make sure Flask is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page center">
      <div className="card auth-card" style={{ width: 430 }}>
        <div className="card-header">
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 14 }}>
            <div
              style={{
                width: 138,
                height: 138,
                borderRadius: 16,
                background: "#ffffff",
                border: "1px solid #d9ece0",
                boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: 12,
                padding: 10,
              }}
            >
              <img src={logo} alt="AllerShield logo" style={{ width: 118, height: 118, objectFit: "contain" }} />
            </div>
            <h2 style={{ margin: 0, fontSize: 30, letterSpacing: 0.2 }}>
              <span style={{ color: "#4f86e8" }}>Aller</span>
              <span style={{ color: "#49a86f" }}>Shield</span>
            </h2>
            <div className="brand-sub" style={{ marginTop: 6 }}>Securely scan product ingredients</div>
          </div>
        </div>

        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button onClick={handleLogin} disabled={loading}>
          {loading ? "Signing in..." : "Login"}
        </button>

        <p className="link" onClick={() => navigate("/register")}>
          Create an account
        </p>
      </div>
    </div>
  );
}


