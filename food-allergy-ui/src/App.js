import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import EditAllergies from "./pages/EditAllergies";
import EducationalResources from "./pages/EducationalResources";
import History from "./pages/History";
import EmergencyHelp from "./pages/EmergencyHelp";
import SmartFAQ from "./pages/SmartFAQ";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/allergies" element={<EditAllergies />} />
        <Route path="/education" element={<EducationalResources />} />
        <Route path="/smart-faq" element={<SmartFAQ />} />
        <Route path="/history" element={<History />} />
        <Route path="/emergency" element={<EmergencyHelp />} />
      </Routes>
    </BrowserRouter>
  );
}
