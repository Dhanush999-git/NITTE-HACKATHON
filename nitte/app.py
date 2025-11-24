from flask import Flask, request, jsonify, send_file, render_template_string
import os
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__, static_folder=".", template_folder=".")

# Try to load model / label encoder / dataset from current folder.
MODEL_PATH = "suitability_model.pkl"
LE_PATH = "label_encoder.pkl"
XLSX_PATH = "Crop_recommendation.xlsx"

model = None
le = None
df = None

if os.path.exists(MODEL_PATH) and os.path.exists(LE_PATH) and os.path.exists(XLSX_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        le = joblib.load(LE_PATH)
        df = pd.read_excel(XLSX_PATH)
        print("Loaded model, encoder, and dataset.")
    except Exception as e:
        print("Warning: failed to load model/encoder/dataset:", e)
        model = None
        le = None
        df = None
else:
    if not os.path.exists(XLSX_PATH):
        print(f"Warning: {XLSX_PATH} not found.")
    if not os.path.exists(MODEL_PATH) or not os.path.exists(LE_PATH):
        print("Warning: model or encoder .pkl not found; using mock.")


@app.route("/")
def home():
    return send_file("index.html")


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json() or {}
    crop_val = data.get("crop", "").strip().lower()

    try:
        temperature = float(data.get("temperature", 0))
        humidity = float(data.get("humidity", 0))
        rainfall = float(data.get("rainfall", 0))
    except Exception:
        return jsonify({"error": "Invalid numeric inputs"}), 400

    if model is not None and le is not None and df is not None:
        X = np.array([[temperature, humidity, rainfall]])
        probs = model.predict_proba(X)[0]
        top_idxs = probs.argsort()[-3:][::-1]
        top_crops = le.inverse_transform(top_idxs)

        # Build response list
        top_list = []
        for idx in top_idxs:
            top_list.append({
                "crop": le.inverse_transform([idx])[0],
                "confidence": float(probs[idx])
            })

        # ⭐ Correct Suitability Logic
        selected_crop_prob = None
        for idx in top_idxs:
            if le.inverse_transform([idx])[0].lower() == crop_val:
                selected_crop_prob = float(probs[idx])
                break

        if selected_crop_prob is not None and selected_crop_prob >= 0.85:
            is_suitable = True
        else:
            is_suitable = False

        best_crop = top_crops[0]

        row = df[df['label'].str.lower() == best_crop.lower()].head(1)
        if not row.empty:
            details = {
                "best_crop": best_crop,
                "temperature": float(row['temperature'].values[0]),
                "humidity": float(row['humidity'].values[0]),
                "rainfall": float(row['rainfall'].values[0])
            }
        else:
            details = {"best_crop": best_crop, "temperature": None, "humidity": None, "rainfall": None}

        return jsonify({
            "crop": crop_val,
            "isSuitable": is_suitable,
            "top_crops": top_list,
            "details": details
        })

    # Fallback mock response
    mock_top = [
        {"crop": "pigeonpeas", "confidence": 0.705},
        {"crop": "papaya", "confidence": 0.155},
        {"crop": "grapes", "confidence": 0.07}
    ]
    mock_details = {
        "best_crop": "pigeonpeas",
        "temperature": 36.512,
        "humidity": 58,
        "rainfall": 123
    }

    is_suitable = (crop_val.lower() == "pigeonpeas")
    return jsonify({
        "crop": crop_val,
        "isSuitable": is_suitable,
        "top_crops": mock_top,
        "details": mock_details
    })


if __name__ == "__main__":
    app.run(debug=True)
