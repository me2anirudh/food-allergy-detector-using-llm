import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";
import api from "../api";

export default function SmartFAQ() {
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "Ask any food-allergy question. I can explain symptoms, label reading, and prevention steps.",
    },
  ]);
  const chatScrollRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages, chatLoading]);

  const sendQuestion = async () => {
    const question = chatInput.trim();
    if (!question) return;

    const next = [...chatMessages, { role: "user", text: question }];
    setChatMessages(next);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await api.askFAQ({ question });
      let json = {};
      try {
        json = await res.json();
      } catch {
        setChatMessages([...next, { role: "assistant", text: `Request failed with status ${res.status}.` }]);
        return;
      }

      if (!res.ok) {
        setChatMessages([...next, { role: "assistant", text: json.message || `Request failed with status ${res.status}.` }]);
        return;
      }

      if (!json.success) {
        setChatMessages([...next, { role: "assistant", text: json.message || "Could not answer right now." }]);
      } else {
        const answer = `${json.answer}\n\n${json.safety_disclaimer}`;
        setChatMessages([...next, { role: "assistant", text: answer }]);
      }
    } catch (err) {
      console.error(err);
      setChatMessages([...next, { role: "assistant", text: "Error contacting FAQ assistant." }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="page">
      <NavBar />
      <div className="container fade-in">
        <h1>Smart FAQ</h1>
        <p>Ask allergy-related questions and get quick educational guidance.</p>

        <div className="tab-links">
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/allergies")}>Edit Allergies</button>
          <button onClick={() => navigate("/education")}>Educational Resources</button>
          <button className="active">Smart FAQ</button>
          <button onClick={() => navigate("/history")}>History</button>
          <button onClick={() => navigate("/emergency")}>Emergency Help</button>
        </div>

        <section>
          <h2>Ask Your Question</h2>
          <div style={{ border: "1px solid #d8e8ff", borderRadius: 8, background: "#f8fbff", padding: 12 }}>
            <div ref={chatScrollRef} style={{ maxHeight: 320, overflowY: "auto", marginBottom: 12 }}>
              {chatMessages.map((m, i) => (
                <div key={i} style={{ marginBottom: 10, textAlign: m.role === "user" ? "right" : "left" }}>
                  <div style={{ display: "inline-block", padding: 12, borderRadius: 8, background: m.role === "user" ? "#dcf3e6" : "#ffffff", border: "1px solid #e1e8f2", whiteSpace: "pre-wrap" }}>
                    {m.text}
                  </div>
                </div>
              ))}
              {chatLoading && <p style={{ margin: 0, color: "#666" }}>Thinking...</p>}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Type your allergy question here..."
                style={{
                  minHeight: 72,
                  height: 72,
                  padding: 12,
                  border: "1px solid #ccd9ea",
                  borderRadius: 6,
                  resize: "none",
                  fontFamily: "inherit",
                  fontSize: 14,
                }}
                maxLength={500}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendQuestion();
                  }
                }}
              />
              <button
                onClick={sendQuestion}
                disabled={chatLoading || !chatInput.trim()}
                style={{ minHeight: 72, height: 72, fontSize: 16, fontWeight: 600 }}
              >
                Ask
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
