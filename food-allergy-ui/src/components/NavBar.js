import React from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

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
    <div className="navbar fade-in">
      <div className="navbar-left">
        <div className="logo">🌿</div>
        <div className="app-name">Food Allergy Scanner</div>
      </div>

      <div className="navbar-center">
        <button className="nav-btn" onClick={() => navigate("/dashboard")}>Dashboard</button>
        <button className="nav-btn" onClick={() => navigate("/allergies")}>Edit Allergies</button>
        <button className="nav-btn" onClick={() => navigate("/education")}>Education</button>
        <button className="nav-btn" onClick={() => navigate("/emergency")}>Emergency</button>
        <button className="nav-btn" onClick={() => navigate("/history")}>History</button>
      </div>

      <div className="navbar-right">
        <button className="secondary small" onClick={logout}>Logout</button>
      </div>
    </div>
  );
}
