from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import pickle
import joblib
import os
import pandas as pd

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ==========================================
# 1. FILE PATHS
# ==========================================

# Current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Crop Prediction & Fertilizer Paths
CROP_MODEL_PATH = os.path.join(BASE_DIR, "XGBoost.pkl")
CROP_LE_PATH = os.path.join(BASE_DIR, "crop_label_encoder.pkl")
FERT_PIPE_PATH = os.path.join(BASE_DIR, "xgb_pipeline.pkl")
FERT_LE_PATH = os.path.join(BASE_DIR, "fertilizer_label_encoder.pkl")
RAIN_CSV = os.path.join(BASE_DIR, "data2.csv")

# Suitability Checker Paths
SUITABILITY_MODEL_PATH = os.path.join(BASE_DIR, "suitability_model.pkl")
SUITABILITY_LE_PATH = os.path.join(BASE_DIR, "label_encoder.pkl") 

# ==========================================
# 2. LOAD MODELS
# ==========================================

# --- Load Crop Prediction Models ---
crop_model = None
crop_le = None
try:
    if os.path.exists(CROP_MODEL_PATH):
        crop_model = pickle.load(open(CROP_MODEL_PATH, "rb"))
        crop_le = pickle.load(open(CROP_LE_PATH, "rb"))
        print("✅ Crop Prediction Models Loaded")
    else:
        print("❌ XGBoost.pkl not found")
except Exception as e:
    print(f"⚠️ Warning (Crop Model): {e}")

# --- Load Fertilizer Models ---
fert_model = None
try:
    if os.path.exists(FERT_PIPE_PATH):
        fert_pipeline = pickle.load(open(FERT_PIPE_PATH, "rb"))
        fert_label_enc = pickle.load(open(FERT_LE_PATH, "rb"))
        soil_le = fert_pipeline["soil_label_encoder"]
        crop_le_f = fert_pipeline["crop_label_encoder"]
        fert_model = fert_pipeline["model"]
        feature_order = fert_pipeline["feature_order"]
        print("✅ Fertilizer Models Loaded")
    else:
        print("❌ Fertilizer pipeline not found")
except Exception as e:
    print(f"⚠️ Warning (Fertilizer Model): {e}")

# --- Load Suitability Models ---
s_model = None
s_le = None
if os.path.exists(SUITABILITY_MODEL_PATH) and os.path.exists(SUITABILITY_LE_PATH):
    try:
        s_model = joblib.load(SUITABILITY_MODEL_PATH)
        s_le = joblib.load(SUITABILITY_LE_PATH)
        print("✅ Suitability Models Loaded")
    except Exception as e:
        print(f"❌ Error loading Suitability models: {e}")
else:
    print("⚠️ Suitability files not found. Using Mock Mode.")

# ==========================================
# 3. LOAD STATE DATA
# ==========================================
try:
    if os.path.exists(RAIN_CSV):
        df_rain = pd.read_csv(RAIN_CSV)
        df_rain.columns = [c.strip() for c in df_rain.columns]
        STATE_COL = next(c for c in df_rain.columns if "state" in c.lower())
        DIST_COL = next(c for c in df_rain.columns if "district" in c.lower())
        df_rain[STATE_COL] = df_rain[STATE_COL].astype(str).str.strip()
        df_rain[DIST_COL] = df_rain[DIST_COL].astype(str).str.strip()
        print("✅ Rainfall CSV Loaded")
    else:
        print("❌ data2.csv not found")
except Exception as e:
    print(f"⚠️ Error loading CSV: {e}")


# ==========================================
# 4. ROUTES
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/crop")
def crop_page():
    return render_template("crop.html")

@app.route("/fertilizer")
def fertilizer_page():
    return render_template("fertilizer.html")

# ==========================================
# 5. API ROUTES
# ==========================================

@app.route("/meta", methods=["GET"])
def meta():
    # Helper to prevent crash if models aren't loaded
    c_classes = list(crop_le.classes_) if crop_le else []
    fc_classes = list(crop_le_f.classes_) if 'crop_le_f' in globals() else []
    s_types = list(soil_le.classes_) if 'soil_le' in globals() else []
    f_order = feature_order if 'feature_order' in globals() else []
    
    return jsonify({
        "crop_classes": c_classes,
        "fert_crop_classes": fc_classes,
        "soil_types": s_types,
        "feature_order": f_order
    })

@app.route("/states", methods=["GET"])
def get_states():
    if 'df_rain' not in globals(): return jsonify({"states": [], "mapping": {}})
    mapping = {}
    states = sorted(df_rain[STATE_COL].unique().tolist())
    for s in states:
        dists = df_rain[df_rain[STATE_COL] == s][DIST_COL].unique().tolist()
        mapping[s] = sorted(dists)
    return jsonify({"states": states, "mapping": mapping})

@app.route("/districts/<state>", methods=["GET"])
def get_districts(state):
    if 'df_rain' not in globals(): return jsonify({"districts": []})
    dists = df_rain[df_rain[STATE_COL] == state][DIST_COL].unique().tolist()
    return jsonify({"districts": sorted(dists)})

# --- 1. CROP PREDICTION API ---
@app.route("/api/predict_crop", methods=["POST"])
def predict_crop():
    if crop_model is None: return jsonify({"error": "Model not loaded"})
    data = request.json
    try:
        x = np.array([[float(data["N"]), float(data["P"]), float(data["K"]),
                       float(data["temperature"]), float(data["humidity"]),
                       float(data["ph"]), float(data["rainfall"])]])
        pred = crop_model.predict(x)[0]
        return jsonify({"recommended_crop": crop_le.inverse_transform([pred])[0]})
    except Exception as e:
        return jsonify({"error": str(e)})

# --- 2. FERTILIZER PREDICTION API ---
@app.route("/predict_fertilizer", methods=["POST"])
def predict_fertilizer():
    if fert_model is None: return jsonify({"error": "Model not loaded"})
    data = request.json
    try:
        soil_enc = soil_le.transform([data["soil_type"]])[0]
        crop_enc = crop_le_f.transform([data["crop"]])[0]

        row = []
        for col in feature_order:
            lc = col.lower()
            if col == "soil_enc": row.append(soil_enc)
            elif col == "crop_enc": row.append(crop_enc)
            elif lc == "nitrogen": row.append(float(data["N"]))
            elif lc.startswith("phospho"): row.append(float(data["P"]))
            elif lc.startswith("potass"): row.append(float(data["K"]))
            elif lc == "moisture": row.append(float(data["moisture"]))
            elif lc == "temperature": row.append(float(data["temperature"]))
            elif lc == "humidity": row.append(float(data["humidity"]))
            else: row.append(0)

        pred = fert_model.predict([row])[0]
        return jsonify({"fertilizer": fert_label_enc.inverse_transform([pred])[0]})
    except Exception as e:
        return jsonify({"error": str(e)})

# --- 3. SUITABILITY CHECKER API ---
@app.route("/check_suitability", methods=["POST"])
def check_suitability():
    data = request.get_json() or {}
    crop_val = data.get("crop", "").strip().lower()

    if s_model is not None and s_le is not None:
        try:
            temp = float(data.get("temperature", 0))
            humid = float(data.get("humidity", 0))
            rain = float(data.get("rainfall", 0))

            X = np.array([[temp, humid, rain]])
            probs = s_model.predict_proba(X)[0]
            
            top_idxs = probs.argsort()[-3:][::-1]
            top_list = []
            for idx in top_idxs:
                top_list.append({
                    "crop": s_le.inverse_transform([idx])[0],
                    "confidence": float(probs[idx])
                })

            is_suitable = False
            classes = s_le.classes_
            if crop_val in classes:
                idx = np.where(classes == crop_val)[0][0]
                if probs[idx] > 0.05:
                    is_suitable = True
            
            return jsonify({"crop": crop_val, "isSuitable": is_suitable, "top_crops": top_list})
        except Exception as e:
            return jsonify({"error": "Prediction failed"}), 400

    # Fallback Mock
    mock_top = [{"crop": "rice", "confidence": 0.85}, {"crop": "maize", "confidence": 0.10}]
    return jsonify({"crop": crop_val, "isSuitable": True, "top_crops": mock_top, "note": "Mock Data"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)