import pickle
import numpy as np

# ---------------- LOAD MODELS ----------------

# Crop Model
crop_model = pickle.load(open("XGBoost.pkl", "rb"))
crop_encoder = pickle.load(open("crop_label_encoder.pkl", "rb"))

# Fertilizer Model
fert_pipeline = pickle.load(open("xgb_pipeline.pkl", "rb"))
fert_label_encoder = pickle.load(open("fertilizer_label_encoder.pkl", "rb"))

print("\n==========================================")
print("   🌾 TWO-MODEL AGRICULTURE SYSTEM (OFFLINE)")
print("==========================================\n")

# --------------------------------------------
# 1️⃣  CROP PREDICTION
# --------------------------------------------
def crop_prediction():
    print("\n🟩 CROP PREDICTION")
    print("----------------------------------")

    state = input("Enter State: ")
    district = input("Enter District: ")

    N = float(input("Enter Nitrogen (N): "))
    P = float(input("Enter Phosphorus (P): "))
    K = float(input("Enter Potassium (K): "))

    temperature = float(input("Enter Temperature (°C): "))
    humidity = float(input("Enter Humidity (%): "))
    ph = float(input("Enter Soil pH: "))
    rainfall = float(input("Enter Rainfall (mm): "))

    # Model input
    arr = np.array([[N, P, K, temperature, humidity, ph, rainfall]])

    # Predict
    idx = crop_model.predict(arr)[0]
    crop_name = crop_encoder.inverse_transform([idx])[0]

    print(f"\n🌾 Recommended Crop: {crop_name}")

    return crop_name


# --------------------------------------------
# 2️⃣  FERTILIZER PREDICTION
# --------------------------------------------
def fertilizer_prediction():
    print("\n🟦 FERTILIZER PREDICTION")
    print("----------------------------------")

    crop_name = input("Enter Crop Name: ")
    soil_type = input("Enter Soil Type (Loamy, Sandy, Clay, etc.): ")

    N = float(input("Enter Nitrogen (N): "))
    P = float(input("Enter Phosphorus (P): "))
    K = float(input("Enter Potassium (K): "))
    moisture = float(input("Enter Soil Moisture (%): "))

    temperature = float(input("Enter Temperature (°C): "))
    humidity = float(input("Enter Humidity (%): "))

    # Extract pipeline parts
    model = fert_pipeline["model"]
    soil_le = fert_pipeline["soil_label_encoder"]
    crop_le = fert_pipeline["crop_label_encoder"]
    order = fert_pipeline["feature_order"]

    # Encode categorical values
    soil_enc = soil_le.transform([soil_type])[0]
    crop_enc = crop_le.transform([crop_name])[0]

    # Build proper model input row following the order
    row = []
    for col in order:
        if col == "soil_enc":
            row.append(soil_enc)
        elif col == "crop_enc":
            row.append(crop_enc)
        elif col == "Nitrogen":
            row.append(N)
        elif col == "Phosphorous":
            row.append(P)
        elif col == "Potassium":
            row.append(K)
        elif col == "Moisture":
            row.append(moisture)
        elif col == "Temperature":
            row.append(temperature)
        elif col == "Humidity":
            row.append(humidity)
        else:
            row.append(0)

    row = np.array([row])

    fert_idx = model.predict(row)[0]
    fert_name = fert_label_encoder.inverse_transform([fert_idx])[0]

    print(f"\n🧪 Recommended Fertilizer: {fert_name}")


# --------------------------------------------
# MAIN PROGRAM FLOW
# --------------------------------------------
selected_crop = crop_prediction()
print("\nNow let's find the best fertilizer...")
fertilizer_prediction()

print("\n==========================================")
print("   ✅ Prediction Completed Successfully!")
print("==========================================")
