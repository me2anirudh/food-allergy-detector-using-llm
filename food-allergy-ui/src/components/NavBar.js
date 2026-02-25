import React from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import logo from "../assets/allershield_logo.png";

export default function NavBar() {
  const navigate = useNavigate();

  const logout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.error(err);
    } finally {
      navigate("/");
    }
  };

  return (
    <div
      className="navbar fade-in"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        width: "100%",
        boxSizing: "border-box",
        zIndex: 1000,
        background: "#1b7f4b",
        color: "#fff",
        padding: "10px 20px",
        margin: 0,
      }}
    >
      <div className="navbar-left" style={{ color: "#fff", display: "flex", alignItems: "center", gap: 10 }}>
        <img
          src={logo}
          alt="AllerShield logo"
          style={{ width: 34, height: 34, objectFit: "contain", borderRadius: 6, background: "#fff", padding: 2 }}
        />
        <div className="app-name" style={{ color: "#fff" }}>AllerShield</div>
      </div>

      <div className="navbar-center" style={{ display: "flex", gap: 10 }}>
        <button className="nav-btn" onClick={() => navigate("/dashboard")}>Dashboard</button>
        <button className="nav-btn" onClick={() => navigate("/allergies")}>Edit Allergies</button>
        <button className="nav-btn" onClick={() => navigate("/education")}>Education</button>
        <button className="nav-btn" onClick={() => navigate("/smart-faq")}>Smart FAQ</button>
        <button className="nav-btn" onClick={() => navigate("/emergency")}>Emergency</button>
        <button className="nav-btn" onClick={() => navigate("/history")}>History</button>
      </div>

      <div className="navbar-right">
        <button className="secondary small" onClick={logout}>Logout</button>
      </div>
    </div>
  );
}
