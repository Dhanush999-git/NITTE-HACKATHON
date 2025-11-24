import joblib
import numpy as np
import pandas as pd

model = joblib.load("suitability_model.pkl")
le = joblib.load("label_encoder.pkl")
df = pd.read_excel("Crop_recommendation.xlsx")

print("\n Multi-Crop Suitability Checker \n")

crop_name = input("Enter crop name you want to grow: ").strip().lower()
temperature = float(input("Enter Temperature (°C): "))
humidity = float(input("Enter Humidity/Moisture (%): "))
rainfall = float(input("Enter Rainfall (mm): "))

input_data = np.array([[temperature, humidity, rainfall]])

# Get prediction probabilities for ALL crops
probs = model.predict_proba(input_data)[0]

# Get top 3 crops
top_indexes = probs.argsort()[-3:][::-1]   # Highest 3
top_crops = le.inverse_transform(top_indexes)

print("\n Top 3 Recommended Crops for these conditions:")
for rank, (crop, p) in enumerate(zip(top_crops, probs[top_indexes]), start=1):
    print(f"{rank}. {crop}  (confidence: {p*100:.2f}%)")

print("\n---------------------------------------------")

# Check if user's crop is suitable
if crop_name in [c.lower() for c in top_crops]:
    print(f"\n YES — '{crop_name}' is suitable for this environment!\n")

    crop_info = df[df['label'].str.lower() == crop_name].head(1)
    print(" Ideal Values for this Crop:")
    print(f"• Temperature: {crop_info['temperature'].values[0]:.2f}")
    print(f"• Humidity: {crop_info['humidity'].values[0]:.2f}")
    print(f"• Rainfall: {crop_info['rainfall'].values[0]:.2f}")

else:
    print(f"\n NO — '{crop_name}' is not among the top suitable crops.")
    print(" Better options exist for this environment.\n")

    print(" Best match crop ideal values:")
    best_crop = top_crops[0]
    crop_data = df[df['label'] == best_crop].head(1)
    print(f"• Temperature: {crop_data['temperature'].values[0]:.2f}")
    print(f"• Humidity: {crop_data['humidity'].values[0]:.2f}")
    print(f"• Rainfall: {crop_data['rainfall'].values[0]:.2f}")

