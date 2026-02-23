###############################
# IMPORTS
###############################
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import re
import time
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import numpy as np
from PIL import Image
import joblib
from dotenv import load_dotenv
from llm_service import (
    generate_personalized_advice,
    generate_alternatives,
    generate_emergency_guidance,
    answer_faq_question,
    LLMServiceError,
)

# Load environment variables from .env
load_dotenv()

###############################
# FLASK APP
###############################
app = Flask(__name__)
app.secret_key = "supersecretkey123"  # change for production

# Use Lax for development with the same-origin dev proxy; set Secure=True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False     # set True in production when using HTTPS
# Accept both common localhost dev ports (3000 & 3001) and their 127.0.0.1 equivalents
CORS(app, supports_credentials=True, origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
])

###############################
# DB CONNECTION
###############################
def get_db():
    return sqlite3.connect("models/users.db", check_same_thread=False)


FAQ_RATE_WINDOW_SECONDS = 60
FAQ_RATE_MAX_REQUESTS = 8
faq_rate_limiter = {}


def _parse_csv_list(text):
    if not text:
        return []
    return [x.strip().lower() for x in str(text).split(",") if x.strip()]


def _get_session_user_allergies():
    if "user_id" not in session:
        return []
    db = get_db()
    user = db.execute(
        "SELECT allergies FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    if not user or not user[0]:
        return []
    return _parse_csv_list(user[0])


def _check_faq_rate_limit(user_key):
    now = time.time()
    window_start = now - FAQ_RATE_WINDOW_SECONDS
    history = faq_rate_limiter.get(user_key, [])
    history = [t for t in history if t >= window_start]
    if len(history) >= FAQ_RATE_MAX_REQUESTS:
        faq_rate_limiter[user_key] = history
        return False
    history.append(now)
    faq_rate_limiter[user_key] = history
    return True


def _local_faq_fallback(question):
    q = (question or "").lower()
    if "anaphylaxis" in q or "severe" in q:
        answer = (
            "Signs of a severe reaction can include trouble breathing, throat tightness, "
            "wheezing, dizziness, fainting, or widespread swelling. Use prescribed epinephrine "
            "immediately and call emergency services."
        )
    elif "symptom" in q:
        answer = (
            "Common allergy symptoms include hives, itching, swelling, stomach pain, vomiting, "
            "cough, wheezing, and breathing difficulty. Severe or rapidly worsening symptoms need urgent care."
        )
    elif "label" in q or "ingredient" in q:
        answer = (
            "Check allergen statements, ingredient lists, and advisory warnings like 'may contain'. "
            "If labeling is unclear, avoid the product."
        )
    else:
        answer = (
            "For food allergy safety, avoid known triggers, read labels carefully, prevent cross-contact, "
            "and keep an emergency action plan with epinephrine if prescribed."
        )

    return {
        "answer": answer,
        "safety_disclaimer": "This is educational information, not medical diagnosis.",
    }

###############################
# REGISTER
###############################
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False}), 400

    username = data.get("username")
    password = data.get("password")

    hashed = generate_password_hash(password)
    db = get_db()

    try:
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        db.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "User exists"}), 409




# LOGIN

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data"}), 400

    username = data.get("username")
    password = data.get("password")

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()

    if user and check_password_hash(user[2], password):
        session["user_id"] = user[0]
        session["username"] = username
        return jsonify({"success": True})

    return jsonify({"success": False, "message": "Invalid credentials"}), 401



###############################
# DASHBOARD
###############################
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session["username"])


###############################
# USER ALLERGIES SETTINGS
###############################
@app.route("/allergies", methods=["GET", "POST"])
def allergies():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    db = get_db()

    if request.method == "POST":
        data = request.get_json()
        if not data or "allergies" not in data:
            return jsonify({"error": "No allergies provided"}), 400

        allergies = data["allergies"].strip().lower()

        db.execute(
            "UPDATE users SET allergies=? WHERE id=?",
            (allergies, session["user_id"])
        )
        db.commit()

        return jsonify({"message": "Allergies saved successfully"})

    # GET request → return saved allergies
    user = db.execute(
        "SELECT allergies FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    return jsonify({
        "allergies": user[0] if user and user[0] else ""
    })



###############################
# LOGOUT
###############################
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


#######################################
# LOAD ML MODELS (FIXED)
#######################################
model = joblib.load("models/allergen_classifier.joblib")
vectorizer = joblib.load("models/tfidf_vectorizer.joblib")
label_binarizer = joblib.load("models/label_binarizer.joblib")

ALLERGEN_LIST = list(label_binarizer.classes_)


#######################################
# CLEAN TEXT
#######################################
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    s = text.lower()
    s = re.sub(r"[^a-z0-9,;()\-/%\s.]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


#######################################
# RESTORED HIGH-QUALITY OCR PIPELINE
#######################################
def ocr_image(image_path: str) -> str:
    """
    Restored OCR pipeline (the one that gave excellent results earlier).
    """
    img = cv2.imread(image_path)
    if img is None:
        return ""

    # Step 1: Convert
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2: Light denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Step 3: Adaptive threshold
    th = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 3
    )

    # Step 4: Upscale
    up = cv2.resize(th, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

    # Best Tesseract config from earlier
    config = "--oem 3 --psm 6"

    text = pytesseract.image_to_string(up, config=config)

    return text


#######################################
# COMBINED HYBRID PREDICTION LOGIC
#######################################
def full_prediction_pipeline(raw_text):
    """
    Run full pipeline and ensure all returned values are native Python types
    so jsonify() won't fail.
    """
    cleaned = clean_text(raw_text)

    # ML probs
    X_vec = vectorizer.transform([cleaned])
    probs = model.predict_proba(X_vec)[0]

    ml_hits = []
    all_probs = []

    # Ensure ALLERGEN_LIST is in sync with label_binarizer.classes_
    # ALLERGEN_LIST = list(label_binarizer.classes_) was set at load time.

    for allergen, p in zip(ALLERGEN_LIST, probs):
        # convert numpy types to native python
        p_float = float(p)
        above = bool(p_float > 0.40)

        all_probs.append({
            "allergen": str(allergen),
            "probability": p_float,
            "above_threshold": above
        })
        if above:
            ml_hits.append(str(allergen))

    # Rule-based
    rule_hits = []
    strong = []
    advisory = []

    lower = cleaned.lower()

    for allergen in ALLERGEN_LIST:
        alg = str(allergen)
        if f"contains {alg}" in lower:
            strong.append(alg)
        if f"may contain {alg}" in lower:
            advisory.append(alg)
        if alg in lower:
            rule_hits.append(alg)

    combined = sorted(list(set(ml_hits + rule_hits + strong + advisory)))

    # User personalization
    personalized = []
    if "user_id" in session:
        db = get_db()
        user = db.execute("SELECT allergies FROM users WHERE id=?",
                          (session["user_id"],)).fetchone()
        if user and user[0]:
            user_allergies = [u.strip().lower() for u in user[0].split(",")]
            personalized = [a for a in combined if a in user_allergies]

    # Ensure all lists contain native Python strings
    result = {
        "input_text": str(raw_text),
        "cleaned_text": str(cleaned),
        "ml_flagged_allergens": [str(x) for x in ml_hits],
        "rule_based_hits": [str(x) for x in rule_hits],
        "strong_contains_allergens": [str(x) for x in strong],
        "advisory_allergens": [str(x) for x in advisory],
        "combined_allergens": [str(x) for x in combined],
        "user_specific_risk": [str(x) for x in personalized],
        "all_allergens_with_probs": all_probs
    }

    return result



###################################
# /predict TEXT ENDPOINT
###################################
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data or "ingredients_text" not in data:
        return jsonify({"error": "ingredients_text field is required"}), 400

    result = full_prediction_pipeline(data["ingredients_text"])
    return jsonify(result)


###################################
# /predict_image ENDPOINT (FULL HYBRID FIXED)
###################################
@app.route("/predict_image", methods=["POST"])
def predict_image():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        img = request.files["image"]
        if not img or not img.filename:
            return jsonify({"error": "Invalid image upload"}), 400

        filename = secure_filename(img.filename)
        print("Received image:", filename)
        filepath = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        img.save(filepath)
        print("Saved to:", filepath)

        ocr_text = ocr_image(filepath)
        if not ocr_text.strip():
            return jsonify({
                "error": "Could not extract text from image. Try a clearer, well-lit ingredient label photo."
            }), 422

        print("OCR text:", ocr_text[:100])
        result = full_prediction_pipeline(ocr_text)
        result["ocr_raw_text"] = ocr_text
        return jsonify(result)
    except pytesseract.TesseractNotFoundError:
        return jsonify({
            "error": "Tesseract OCR is not installed or not found at configured path."
        }), 500
    except Exception as e:
        print(f"predict_image error: {str(e)}")
        return jsonify({"error": f"Scan processing failed: {str(e)}"}), 500


@app.route("/save_scan", methods=["POST"])
def save_scan():
    print("Save scan called")
    if "user_id" not in session:
        print("No user_id in session")
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    print("Data:", data)
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    product_name = data.get("product_name")
    ingredients = data.get("ingredients", "")
    result = data.get("result")
    allergens_found = data.get("allergens_found", "")

    if not product_name or not result:
        return jsonify({"success": False, "message": "Product name and result are required"}), 400

    user_id = session["user_id"]
    print("User ID:", user_id)

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO scan_history (user_id, product_name, ingredients, result, allergens_found)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, product_name, ingredients, result, allergens_found))
        conn.commit()
        conn.close()
        print("Saved successfully")
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        print("IntegrityError: Product name exists")
        return jsonify({"success": False, "message": "Product name already exists"}), 400
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/get_history", methods=["GET"])
def get_history():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    user_id = session["user_id"]

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT product_name, ingredients, result, allergens_found, timestamp
            FROM scan_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "product_name": row[0],
                "ingredients": row[1],
                "result": row[2],
                "allergens_found": row[3],
                "timestamp": row[4]
            })

        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/get_ai_advice", methods=["POST"])
def get_ai_advice():
    """Backward-compatible advice endpoint returning summary text."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    allergens = data.get("allergens_found", "")
    product_name = data.get("product_name", "this product")
    user_allergies = data.get("user_allergies", "")
    ingredients_text = data.get("ingredients_text", "")

    if not allergens:
        return jsonify({"success": True, "advice": "No allergens detected. This product appears to be safe for you!"})

    try:
        payload = generate_personalized_advice(
            product_name=product_name,
            detected_allergens=_parse_csv_list(allergens),
            user_allergies=_parse_csv_list(user_allergies) or _get_session_user_allergies(),
            ingredients_text=ingredients_text,
        )
        advice = f"{payload['verdict_summary']} {payload['risk_explanation']}".strip()
        return jsonify({"success": True, "advice": advice, "details": payload})
    except LLMServiceError as e:
        print(f"Error in get_ai_advice: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        print(f"Unexpected error in get_ai_advice: {str(e)}")
        return jsonify({"success": False, "message": "Unexpected error while generating advice"}), 500


@app.route("/llm/personalized_advice", methods=["POST"])
def llm_personalized_advice():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json() or {}
    product_name = (data.get("product_name") or "this product").strip()
    detected_allergens = data.get("detected_allergens") or []
    ingredients_text = data.get("ingredients_text") or ""

    if isinstance(detected_allergens, str):
        detected_allergens = _parse_csv_list(detected_allergens)
    else:
        detected_allergens = [str(x).strip().lower() for x in detected_allergens if str(x).strip()]

    user_allergies = _get_session_user_allergies()

    try:
        advice = generate_personalized_advice(
            product_name=product_name,
            detected_allergens=detected_allergens,
            user_allergies=user_allergies,
            ingredients_text=ingredients_text,
        )
        return jsonify({"success": True, "advice": advice})
    except LLMServiceError as e:
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500


@app.route("/llm/alternatives", methods=["POST"])
def llm_alternatives():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json() or {}
    product_name = (data.get("product_name") or "this product").strip()
    detected_allergens = data.get("detected_allergens") or []

    if isinstance(detected_allergens, str):
        detected_allergens = _parse_csv_list(detected_allergens)
    else:
        detected_allergens = [str(x).strip().lower() for x in detected_allergens if str(x).strip()]

    user_allergies = _get_session_user_allergies()

    try:
        alternatives = generate_alternatives(
            product_name=product_name,
            detected_allergens=detected_allergens,
            user_allergies=user_allergies,
        )
        return jsonify({"success": True, **alternatives})
    except LLMServiceError as e:
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500


@app.route("/llm/emergency_guidance", methods=["POST"])
def llm_emergency_guidance():
    data = request.get_json() or {}

    suspected_allergen = (data.get("suspected_allergen") or "").strip()
    symptoms = (data.get("symptoms") or "").strip()
    has_epinephrine = (data.get("has_epinephrine") or "unknown").strip().lower()
    age_group = (data.get("age_group") or "adult").strip().lower()

    if not symptoms:
        return jsonify({"success": False, "message": "symptoms is required"}), 400

    try:
        guidance = generate_emergency_guidance(
            suspected_allergen=suspected_allergen or "unknown",
            symptoms=symptoms,
            has_epinephrine=has_epinephrine,
            age_group=age_group,
        )
        return jsonify({"success": True, "guidance": guidance})
    except LLMServiceError as e:
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500


@app.route("/llm/faq", methods=["POST"])
def llm_faq():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"success": False, "message": "question is required"}), 400
    if len(question) > 500:
        return jsonify({"success": False, "message": "Question is too long. Keep it under 500 characters."}), 400

    blocked_terms = ["ignore previous", "system prompt", "jailbreak", "bypass", "dosage"]
    q_lower = question.lower()
    if any(term in q_lower for term in blocked_terms):
        return jsonify({"success": False, "message": "Question contains disallowed content."}), 400

    user_key = str(session.get("user_id", request.remote_addr or "anon"))
    if not _check_faq_rate_limit(user_key):
        return jsonify({"success": False, "message": "Too many requests. Please wait a minute and try again."}), 429

    try:
        answer = answer_faq_question(question=question, user_allergies=_get_session_user_allergies())
        return jsonify({"success": True, **answer})
    except LLMServiceError as e:
        print(f"FAQ LLM unavailable: {str(e)}")
        fallback = _local_faq_fallback(question)
        return jsonify({"success": True, **fallback})
    except Exception as e:
        print(f"Unexpected FAQ error: {str(e)}")
        fallback = _local_faq_fallback(question)
        return jsonify({"success": True, **fallback})


@app.route("/")
def home():
    return redirect(url_for("login"))



###################################
# RUN APP
###################################
if __name__ == "__main__":
    app.run(debug=True)
