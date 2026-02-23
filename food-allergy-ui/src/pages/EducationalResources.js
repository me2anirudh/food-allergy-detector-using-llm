import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";

export default function EducationalResources() {
  const [searchTerm, setSearchTerm] = useState("");
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
          <button onClick={() => navigate("/smart-faq")}>Smart FAQ</button>
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
