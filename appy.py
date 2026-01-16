# ###############################
# # IMPORTS
# ###############################
# from flask import Flask, request, jsonify, render_template, redirect, url_for, session
# from werkzeug.security import generate_password_hash, check_password_hash
# import sqlite3
# import os
# import re
# import cv2
# import pytesseract
# import joblib

# ###############################
# # FLASK APP
# ###############################
# app = Flask(__name__)
# app.secret_key = "supersecretkey123"  # change in production

# ###############################
# # DATABASE
# ###############################
# def get_db():
#     return sqlite3.connect("models/users.db", check_same_thread=False)

# ###############################
# # AUTH ROUTES
# ###############################
# @app.route("/", methods=["GET"])
# def home():
#     return redirect(url_for("login"))

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]

#         hashed = generate_password_hash(password)
#         db = get_db()

#         try:
#             db.execute(
#                 "INSERT INTO users (username, password) VALUES (?, ?)",
#                 (username, hashed)
#             )
#             db.commit()
#             return redirect(url_for("login"))
#         except sqlite3.IntegrityError:
#             return "Username already exists"

#     return render_template("register.html")

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]

#         db = get_db()
#         user = db.execute(
#             "SELECT * FROM users WHERE username=?",
#             (username,)
#         ).fetchone()

#         if user and check_password_hash(user[2], password):
#             session["user_id"] = user[0]
#             session["username"] = username
#             return redirect(url_for("dashboard"))

#         return "Invalid credentials"

#     return render_template("login.html")

# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect(url_for("login"))

# ###############################
# # DASHBOARD
# ###############################
# @app.route("/dashboard")
# def dashboard():
#     if "user_id" not in session:
#         return redirect(url_for("login"))

#     return render_template(
#         "dashboard.html",
#         username=session["username"]
#     )

# ###############################
# # ALLERGIES SETTINGS
# ###############################
# @app.route("/allergies", methods=["GET", "POST"])
# def allergies():
#     if "user_id" not in session:
#         return redirect(url_for("login"))

#     db = get_db()

#     if request.method == "POST":
#         allergies = request.form["allergies"].strip().lower()
#         db.execute(
#             "UPDATE users SET allergies=? WHERE id=?",
#             (allergies, session["user_id"])
#         )
#         db.commit()
#         return redirect(url_for("dashboard"))

#     user = db.execute(
#         "SELECT allergies FROM users WHERE id=?",
#         (session["user_id"],)
#     ).fetchone()

#     return render_template(
#         "allergies.html",
#         allergies=user[0] if user and user[0] else ""
#     )

# ###############################
# # LOAD ML MODELS
# ###############################
# model = joblib.load("models/allergen_classifier.joblib")
# vectorizer = joblib.load("models/tfidf_vectorizer.joblib")
# label_binarizer = joblib.load("models/label_binarizer.joblib")

# ALLERGEN_LIST = list(label_binarizer.classes_)

# ###############################
# # TEXT CLEANING
# ###############################
# def clean_text(text):
#     if not isinstance(text, str):
#         return ""
#     text = text.lower()
#     text = re.sub(r"[^a-z0-9,;().\s]", " ", text)
#     text = re.sub(r"\s+", " ", text)
#     return text.strip()

# ###############################
# # OCR PIPELINE (STABLE)
# ###############################
# def ocr_image(image_path):
#     img = cv2.imread(image_path)
#     if img is None:
#         return ""

#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     denoised = cv2.fastNlMeansDenoising(gray, h=10)

#     thresh = cv2.adaptiveThreshold(
#         denoised, 255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         31, 3
#     )

#     upscaled = cv2.resize(
#         thresh, None, fx=2, fy=2,
#         interpolation=cv2.INTER_LINEAR
#     )

#     text = pytesseract.image_to_string(
#         upscaled,
#         config="--oem 3 --psm 6"
#     )

#     return text

# ###############################
# # HYBRID PREDICTION
# ###############################
# def hybrid_predict(text):
#     cleaned = clean_text(text)

#     X = vectorizer.transform([cleaned])
#     probs = model.predict_proba(X)[0]

#     detected = []

#     for allergen, p in zip(ALLERGEN_LIST, probs):
#         if float(p) > 0.40:
#             detected.append(allergen)

#     for allergen in ALLERGEN_LIST:
#         if allergen in cleaned:
#             detected.append(allergen)

#     detected = sorted(set(detected))

#     user_risk = []
#     db = get_db()
#     user = db.execute(
#         "SELECT allergies FROM users WHERE id=?",
#         (session["user_id"],)
#     ).fetchone()

#     if user and user[0]:
#         user_allergies = [
#             a.strip() for a in user[0].split(",")
#         ]
#         user_risk = [
#             a for a in detected if a in user_allergies
#         ]

#     return detected, user_risk

# ###############################
# # IMAGE UPLOAD + RESULT PAGE
# ###############################
# @app.route("/scan", methods=["POST"])
# def scan():
#     if "user_id" not in session:
#         return redirect(url_for("login"))

#     if "image" not in request.files:
#         return "No image uploaded"

#     image = request.files["image"]
#     os.makedirs("uploads", exist_ok=True)
#     path = os.path.join("uploads", image.filename)
#     image.save(path)

#     ocr_text = ocr_image(path)
#     detected, user_risk = hybrid_predict(ocr_text)

#     if user_risk:
#         status = "UNSAFE"
#         message = f"Contains allergens you are allergic to: {', '.join(user_risk)}"
#     else:
#         status = "SAFE"
#         message = "No allergens detected from your allergy profile"

#     return render_template(
#         "result.html",
#         status=status,
#         message=message,
#         detected=detected
#     )

# ###############################
# # RUN
# ###############################
# if __name__ == "__main__":
#     app.run(debug=True)
