import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load dataset
df = pd.read_excel("Crop_recommendation.xlsx")

# Features
X = df[['temperature', 'humidity', 'rainfall']]

# Target is the crop name
y = df['label']

# Encode crop names
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42
)

# Train a model to classify the best crop based on conditions
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# Save model + encoder
joblib.dump(model, "suitability_model.pkl")
joblib.dump(le, "label_encoder.pkl")

print("Model trained and saved!")
