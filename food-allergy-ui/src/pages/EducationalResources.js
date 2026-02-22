import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";
import api from "../api";

export default function EducationalResources() {
  const [searchTerm, setSearchTerm] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "Ask any food-allergy question. I can explain symptoms, label reading, and prevention steps.",
    },
  ]);
  const navigate = useNavigate();

  const allergens = [
    { name: "Peanuts", symptoms: "Hives, swelling, difficulty breathing, anaphylaxis", prevalence: "Affects 1-2% of children; often lifelong", prevention: "Avoid all peanut products; check labels carefully" },
    { name: "Tree Nuts", symptoms: "Similar to peanuts; can be severe", prevalence: "Affects about 1% of the population", prevention: "Avoid almonds, walnuts, etc.; cross-contamination common" },
    { name: "Milk", symptoms: "Digestive issues, skin rashes, respiratory problems", prevalence: "Affects 2-3% of infants; many outgrow it", prevention: "Use alternatives like almond milk; read labels" },
    { name: "Eggs", symptoms: "Skin reactions, gastrointestinal issues", prevalence: "Affects 1-2% of young children; often outgrown", prevention: "Avoid baked goods; check for egg derivatives" },
    { name: "Wheat/Gluten", symptoms: "Bloating, diarrhea, skin issues (celiac disease)", prevalence: "Celiac affects 1% of people", prevention: "Gluten-free diet; avoid cross-contamination" },
    { name: "Soy", symptoms: "Hives, vomiting, anaphylaxis", prevalence: "Affects less than 1% of children", prevention: "Avoid soy products; hidden in many foods" },
    { name: "Fish/Shellfish", symptoms: "Severe reactions common; can be life-threatening", prevalence: "Affects 1-2% of adults", prevention: "Avoid all seafood; restaurant caution advised" },
  ];

  const faqs = [
    { question: "What is a food allergy?", answer: "A food allergy is an immune system reaction to a food protein. Symptoms can range from mild hives to severe anaphylaxis." },
    { question: "How is it different from food intolerance?", answer: "Food intolerance usually does not involve the immune system and is generally less dangerous than allergy." },
    { question: "Can food allergies be cured?", answer: "Some allergies are outgrown, while others persist. Discuss long-term management with an allergist." },
    { question: "What should I do if I suspect an allergy?", answer: "Get evaluated by an allergist and follow a medical action plan if diagnosed." },
    { question: "How can I prevent allergic reactions?", answer: "Read labels, avoid cross-contact, and inform food handlers about your allergies." },
  ];

  const filteredAllergens = allergens.filter((allergen) => allergen.name.toLowerCase().includes(searchTerm.toLowerCase()));

  const sendQuestion = async () => {
    const question = chatInput.trim();
    if (!question) return;

    const next = [...chatMessages, { role: "user", text: question }];
    setChatMessages(next);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await api.askFAQ({ question });
      const json = await res.json();
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
        <h1>Educational Resources</h1>
        <p>Learn about food allergies, common allergens, and safe habits.</p>

        <div className="tab-links">
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/allergies")}>Edit Allergies</button>
          <button className="active">Educational Resources</button>
          <button onClick={() => navigate("/history")}>History</button>
          <button onClick={() => navigate("/emergency")}>Emergency Help</button>
        </div>

        <section>
          <h2>Allergen Database</h2>
          <input
            type="text"
            placeholder="Search allergens (e.g., peanuts)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <div className="allergen-list">
            {filteredAllergens.map((allergen, index) => (
              <div key={index} className="allergen-card">
                <h3>{allergen.name}</h3>
                <p><strong>Symptoms:</strong> {allergen.symptoms}</p>
                <p><strong>Prevalence:</strong> {allergen.prevalence}</p>
                <p><strong>Prevention Tips:</strong> {allergen.prevention}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2>Smart FAQ Chat</h2>
          <div style={{ border: "1px solid #d8e8ff", borderRadius: 8, background: "#f8fbff", padding: 12 }}>
            <div style={{ maxHeight: 260, overflowY: "auto", marginBottom: 10 }}>
              {chatMessages.map((m, i) => (
                <div key={i} style={{ marginBottom: 8, textAlign: m.role === "user" ? "right" : "left" }}>
                  <div style={{ display: "inline-block", padding: 10, borderRadius: 8, background: m.role === "user" ? "#dcf3e6" : "#ffffff", border: "1px solid #e1e8f2", whiteSpace: "pre-wrap" }}>
                    {m.text}
                  </div>
                </div>
              ))}
              {chatLoading && <p style={{ margin: 0, color: "#666" }}>Thinking...</p>}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="What are signs of anaphylaxis?"
                style={{ flex: 1, padding: 10, border: "1px solid #ccd9ea", borderRadius: 6 }}
                maxLength={500}
                onKeyDown={(e) => e.key === "Enter" && sendQuestion()}
              />
              <button onClick={sendQuestion} disabled={chatLoading || !chatInput.trim()}>Ask</button>
            </div>
          </div>
        </section>

        <section>
          <h2>FAQs & Tips</h2>
          <div className="faq-list">
            {faqs.map((faq, index) => (
              <div key={index} className="faq-item">
                <h3>{faq.question}</h3>
                <p>{faq.answer}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
