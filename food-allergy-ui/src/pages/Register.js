import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async () => {
    setLoading(true);
    try {
      const res = await api.register({ username, password });
      const data = await res.json();

      if (res.ok && data.success) {
        alert("Account created successfully");
        navigate("/");
      } else {
        alert(data.message || "User already exists");
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
      <div className="card auth-card">
        <div className="card-header">
          <div>
            <h2>Create Account</h2>
            <div className="brand-sub">Set up your account</div>
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

        <button onClick={handleRegister} disabled={loading}>
          {loading ? "Creating..." : "Register"}
        </button>

        <p className="link" onClick={() => navigate("/")}>
          Back to login
        </p>
      </div>
    </div>
  );
}

