###############################
# IMPORTS
###############################
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import re
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import numpy as np
from PIL import Image
import joblib

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
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    img = request.files["image"]
    print("Received image:", img.filename)
    filepath = os.path.join("uploads", img.filename)
    os.makedirs("uploads", exist_ok=True)
    img.save(filepath)
    print("Saved to:", filepath)

    ocr_text = ocr_image(filepath)
    print("OCR text:", ocr_text[:100])
    result = full_prediction_pipeline(ocr_text)
    result["ocr_raw_text"] = ocr_text

    return jsonify(result)


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


@app.route("/")
def home():
    return redirect(url_for("login"))



###################################
# RUN APP
###################################
if __name__ == "__main__":
    app.run(debug=True)
