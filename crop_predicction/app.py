from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pickle
import os
import pandas as pd

app = Flask(__name__)
CORS(app)

# ---------------- FILE PATHS ----------------
CROP_MODEL_PATH = "XGBoost.pkl"
CROP_LE_PATH = "crop_label_encoder.pkl"
FERT_PIPE_PATH = "xgb_pipeline.pkl"
FERT_LE_PATH = "fertilizer_label_encoder.pkl"
RAIN_CSV = "data2.csv"     # <-- correct rainfall/state–district file


# ---------------- LOAD MODELS ----------------
for p in [CROP_MODEL_PATH, CROP_LE_PATH, FERT_PIPE_PATH, FERT_LE_PATH]:
    if not os.path.exists(p):
        raise FileNotFoundError(f"Model file missing: {p}")

crop_model = pickle.load(open(CROP_MODEL_PATH, "rb"))
crop_le = pickle.load(open(CROP_LE_PATH, "rb"))

fert_pipeline = pickle.load(open(FERT_PIPE_PATH, "rb"))
fert_label_enc = pickle.load(open(FERT_LE_PATH, "rb"))

soil_le = fert_pipeline["soil_label_encoder"]
crop_le_f = fert_pipeline["crop_label_encoder"]
fert_model = fert_pipeline["model"]
feature_order = fert_pipeline["feature_order"]

# ---------------- LOAD STATE & DISTRICT DATA ----------------
df_rain = pd.read_csv(RAIN_CSV)

# Clean column names
df_rain.columns = [c.strip() for c in df_rain.columns]

# Detect correct columns
STATE_COL = None
DIST_COL = None

for c in df_rain.columns:
    lc = c.lower()
    if "state" in lc:
        STATE_COL = c
    if "district" in lc:
        DIST_COL = c

if STATE_COL is None or DIST_COL is None:
    print("❌ ERROR: Could not detect state/district columns")
    print(df_rain.columns)
    raise SystemExit


# Ensure strings
df_rain[STATE_COL] = df_rain[STATE_COL].astype(str).str.strip()
df_rain[DIST_COL] = df_rain[DIST_COL].astype(str).str.strip()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return jsonify({"status": "OK", "message": "Flask backend running"})


# ---------------- META ----------------
@app.route("/meta", methods=["GET"])
def meta():
    return jsonify({
        "crop_classes": list(crop_le.classes_),
        "fert_crop_classes": list(crop_le_f.classes_),
        "soil_types": list(soil_le.classes_),
        "feature_order": feature_order
    })


# ---------------- STATES API ----------------
@app.route("/states", methods=["GET"])
def get_states():

    mapping = {}
    states = sorted(df_rain[STATE_COL].unique().tolist())

    for st in states:
        districts = df_rain[df_rain[STATE_COL] == st][DIST_COL].unique().tolist()
        mapping[st] = sorted(districts)

    return jsonify({
        "states": states,
        "mapping": mapping
    })


# ---------------- DISTRICTS API ----------------
@app.route("/districts/<state>", methods=["GET"])
def get_districts(state):
    d = df_rain[df_rain[STATE_COL] == state][DIST_COL].dropna().unique().tolist()
    return jsonify({"districts": sorted(d)})


# ---------------- CROP PREDICTION ----------------
@app.route("/predict_crop", methods=["POST"])
def predict_crop():
    try:
        data = request.json

        x = np.array([[
            float(data["N"]),
            float(data["P"]),
            float(data["K"]),
            float(data["temperature"]),
            float(data["humidity"]),
            float(data["ph"]),
            float(data["rainfall"])
        ]])

        pred_idx = crop_model.predict(x)[0]
        crop_name = crop_le.inverse_transform([pred_idx])[0]

        return jsonify({"crop": crop_name})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- FERTILIZER PREDICTION ----------------
@app.route("/predict_fertilizer", methods=["POST"])
def predict_fertilizer():
    try:
        data = request.json

        crop = data["crop"]
        soil = data["soil_type"]

        if crop not in crop_le_f.classes_:
            return jsonify({"error": f"Unknown crop: {crop}"}), 400
        if soil not in soil_le.classes_:
            return jsonify({"error": f"Unknown soil type: {soil}"}), 400

        soil_enc = soil_le.transform([soil])[0]
        crop_enc = crop_le_f.transform([crop])[0]

        row = []
        for col in feature_order:
            if col == "soil_enc":
                row.append(soil_enc)
            elif col == "crop_enc":
                row.append(crop_enc)
            else:
                if col.lower() == "nitrogen":
                    row.append(float(data["N"]))
                elif col.lower().startswith("phospho"):
                    row.append(float(data["P"]))
                elif col.lower().startswith("potass"):
                    row.append(float(data["K"]))
                elif col.lower() == "moisture":
                    row.append(float(data["moisture"]))
                elif col.lower() == "temperature":
                    row.append(float(data["temperature"]))
                elif col.lower() == "humidity":
                    row.append(float(data["humidity"]))
                else:
                    row.append(0)

        x = np.array([row])
        pred = fert_model.predict(x)[0]
        fert_name = fert_label_enc.inverse_transform([pred])[0]

        return jsonify({"fertilizer": fert_name})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
