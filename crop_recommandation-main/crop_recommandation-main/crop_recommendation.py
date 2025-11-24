# train_all_models.py
# Combined training script for:
#  - Crop model (crop_recommendation.csv) -> XGBoost.pkl, crop_label_encoder.pkl
#  - Fertilizer model (Fertilizer Prediction.csv) -> xgb_pipeline.pkl, fertilizer_label_encoder.pkl
#  - Saves cleaned rainfall CSV from data2.csv -> rainfall_dataset_cleaned.csv

from __future__ import print_function
import os, sys
import pandas as pd, numpy as np, pickle, warnings
warnings.filterwarnings("ignore")

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

# Filenames used in your folder (from your screenshot)
CROP_CSV = "crop_recommendation.csv"
FERT_CSV = "Fertilizer Prediction.csv"
RAIN_CSV = "data2.csv"

OUT_CROP_MODEL = "XGBoost.pkl"
OUT_CROP_LE = "crop_label_encoder.pkl"
OUT_FERT_PIPE = "xgb_pipeline.pkl"
OUT_FERT_LE = "fertilizer_label_encoder.pkl"
OUT_RAIN = "rainfall_dataset_cleaned.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2

def ensure_exists(path):
    if not os.path.exists(path):
        print(f"ERROR: required file not found -> {path}")
        sys.exit(1)

# -------------- check files --------------
ensure_exists(CROP_CSV)
ensure_exists(FERT_CSV)
ensure_exists(RAIN_CSV)

print("Loading datasets...")
df_crop = pd.read_csv(CROP_CSV)
df_fert = pd.read_csv(FERT_CSV)
df_rain = pd.read_csv(RAIN_CSV)

print("Shapes:", "crop:", df_crop.shape, "fert:", df_fert.shape, "rain:", df_rain.shape)

# ------------------ CROP MODEL ------------------
print("\n=== TRAINING CROP MODEL ===")
# Expect columns: N, P, K, temperature, humidity, ph, rainfall, label
# Normalize column names to exact lowercase canonical if necessary
cols_lower = {c.lower(): c for c in df_crop.columns}
expected = ['n','p','k','temperature','humidity','ph','rainfall','label']
missing = [e for e in expected if e not in cols_lower]
if missing:
    print("Crop CSV missing columns:", missing)
    # Try common mapping (if your column names are capitalized exactly it's OK already)
    # If still missing, fail
    # We will check the exact names present and abort if required columns not present
    sys.exit(1)

# Rename to canonical lower names for easy access
df_crop = df_crop.rename(columns={cols_lower[k]: k for k in cols_lower if k in expected})
# Ensure numeric types
for c in ['n','p','k','temperature','humidity','ph','rainfall']:
    df_crop[c] = pd.to_numeric(df_crop[c], errors='coerce')

df_crop = df_crop.dropna(subset=['n','p','k','temperature','humidity','ph','rainfall','label']).reset_index(drop=True)
print("Crop rows after dropna:", df_crop.shape[0])

# Label encode crop labels
crop_le = LabelEncoder()
df_crop['label_enc'] = crop_le.fit_transform(df_crop['label'].astype(str))
pickle.dump(crop_le, open(OUT_CROP_LE, "wb"))

# Prepare X,y and split
X_crop = df_crop[['n','p','k','temperature','humidity','ph','rainfall']].values
y_crop = df_crop['label_enc'].astype(int).values

Xc_train, Xc_test, yc_train, yc_test = train_test_split(
    X_crop, y_crop, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_crop
)

crop_model = xgb.XGBClassifier(
    objective='multi:softprob', eval_metric='mlogloss', use_label_encoder=False,
    n_estimators=200, random_state=RANDOM_STATE, verbosity=0
)
print("Fitting crop model...")
crop_model.fit(Xc_train, yc_train)
yc_pred = crop_model.predict(Xc_test)
print("Crop accuracy:", accuracy_score(yc_test, yc_pred))
print(classification_report(yc_test, yc_pred, target_names=crop_le.classes_))
pickle.dump(crop_model, open(OUT_CROP_MODEL, "wb"))
print("Saved crop model and encoder:", OUT_CROP_MODEL, OUT_CROP_LE)

# ------------------ FERTILIZER MODEL ------------------
print("\n=== TRAINING FERTILIZER MODEL ===")
# Clean fertilizer column names (strip whitespace)
df_fert = df_fert.rename(columns=lambda s: s.strip() if isinstance(s, str) else s)

# Normalize potential typos and map:
# Observed columns in your uploaded file: 'Temparature', 'Humidity ', 'Moisture', 'Soil Type', 'Crop Type', 'Nitrogen', 'Potassium', 'Phosphorous', 'Fertilizer Name'
# Map common variants to canonical names
col_map = {}
if 'Temparature' in df_fert.columns: col_map['Temparature'] = 'Temperature'
if 'Humidity ' in df_fert.columns: col_map['Humidity '] = 'Humidity'
if 'Phosphorous' in df_fert.columns: col_map['Phosphorous'] = 'Phosphorous'
df_fert = df_fert.rename(columns=col_map)

# Required categorical columns
req_cats = ['Soil Type','Crop Type','Fertilizer Name']
for c in req_cats:
    if c not in df_fert.columns:
        print(f"ERROR: Fertilizer CSV missing required column: {c}")
        sys.exit(1)

# Detect numeric nutrient columns available
possible_numerics = ['Nitrogen','Phosphorous','Potassium','N','P','K','Moisture','Temperature','Humidity']
present_numerics = [c for c in possible_numerics if c in df_fert.columns]
print("Detected fertilizer numeric columns:", present_numerics)

# Build fertilizer feature order:
fert_features = ['Soil Type','Crop Type']
if 'Moisture' in df_fert.columns:
    fert_features.append('Moisture')
# Add nutrients in a preferred order if present
for nutrient in ['Nitrogen','Phosphorous','Potassium','N','P','K','Temperature','Humidity']:
    if nutrient in df_fert.columns and nutrient not in fert_features:
        fert_features.append(nutrient)

print("Final fertilizer feature order (readable):", fert_features)

# Drop rows with missing target
df_fert = df_fert.dropna(subset=['Fertilizer Name']).reset_index(drop=True)

# Encode categorical columns
soil_le = LabelEncoder()
crop_le_f = LabelEncoder()
fert_le = LabelEncoder()

df_fert['soil_enc'] = soil_le.fit_transform(df_fert['Soil Type'].astype(str))
df_fert['crop_enc'] = crop_le_f.fit_transform(df_fert['Crop Type'].astype(str))
df_fert['fert_enc'] = fert_le.fit_transform(df_fert['Fertilizer Name'].astype(str))
pickle.dump(fert_le, open(OUT_FERT_LE, "wb"))

# Construct model input columns (replace Soil Type & Crop Type with encodings)
model_feature_cols = []
for f in fert_features:
    if f == 'Soil Type':
        model_feature_cols.append('soil_enc')
    elif f == 'Crop Type':
        model_feature_cols.append('crop_enc')
    else:
        model_feature_cols.append(f)

# Validate model_feature_cols exist
for col in model_feature_cols:
    if col not in df_fert.columns and col not in ['soil_enc','crop_enc']:
        print("Missing feature in fertilizer CSV:", col)
        sys.exit(1)

Xf = df_fert[model_feature_cols].copy()
# ensure numeric
Xf = Xf.apply(pd.to_numeric, errors='coerce').fillna(0)
y_f = df_fert['fert_enc'].values

Xf_train, Xf_test, yf_train, yf_test = train_test_split(
    Xf.values, y_f, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_f
)

fert_model = xgb.XGBClassifier(
    objective='multi:softprob', eval_metric='mlogloss', use_label_encoder=False,
    n_estimators=200, random_state=RANDOM_STATE, verbosity=0
)
print("Fitting fertilizer model...")
fert_model.fit(Xf_train, yf_train)

yf_pred = fert_model.predict(Xf_test)
print("Fertilizer accuracy:", accuracy_score(yf_test, yf_pred))
print(classification_report(yf_test, yf_pred, target_names=fert_le.classes_))

# Save pipeline dict (encoders + model + feature order as model expects)
pipeline = {
    "soil_label_encoder": soil_le,
    "crop_label_encoder": crop_le_f,
    "fert_label_encoder": fert_le,
    "feature_order": model_feature_cols,   # e.g. ['soil_enc','crop_enc','Moisture','Nitrogen',...]
    "model": fert_model
}
pickle.dump(pipeline, open(OUT_FERT_PIPE, "wb"))
print("Saved fertilizer pipeline and encoder:", OUT_FERT_PIPE, OUT_FERT_LE)

# ------------------ save rainfall data ------------------
df_rain.to_csv(OUT_RAIN, index=False)
print("Saved rainfall lookup:", OUT_RAIN)

# ------------------ helper functions (example usage) ------------------
def predict_crop_local(N,P,K,temperature,humidity,ph,rainfall):
    model = pickle.load(open(OUT_CROP_MODEL,"rb"))
    le = pickle.load(open(OUT_CROP_LE,"rb"))
    x = np.array([[N,P,K,temperature,humidity,ph,rainfall]])
    pred_idx = model.predict(x)[0]
    return le.inverse_transform([int(pred_idx)])[0]

def predict_fertilizer_local(soil, crop, numeric_dict):
    pl = pickle.load(open(OUT_FERT_PIPE,"rb"))
    soil_le = pl['soil_label_encoder']
    crop_le = pl['crop_label_encoder']
    fert_le = pl['fert_label_encoder']
    order = pl['feature_order']
    model = pl['model']
    # build row
    soil_enc = soil_le.transform([soil])[0] if isinstance(soil,str) else int(soil)
    crop_enc = crop_le.transform([crop])[0] if isinstance(crop,str) else int(crop)
    row = []
    for col in order:
        if col == 'soil_enc':
            row.append(soil_enc)
        elif col == 'crop_enc':
            row.append(crop_enc)
        else:
            row.append(float(numeric_dict.get(col, 0)))
    x = np.array([row])
    pred_idx = model.predict(x)[0]
    return fert_le.inverse_transform([int(pred_idx)])[0]

print("\nTraining completed. Models saved:")
print(" - Crop model:", OUT_CROP_MODEL)
print(" - Crop label encoder:", OUT_CROP_LE)
print(" - Fertilizer pipeline:", OUT_FERT_PIPE)
print(" - Fertilizer label encoder:", OUT_FERT_LE)
print(" - Rainfall CSV:", OUT_RAIN)
print("\nExample function usage (python):")
print("  from train_all_models import predict_crop_local, predict_fertilizer_local")
print("  predict_crop_local(90,42,43,20.8,82,6.5,202.9)")
print("  predict_fertilizer_local('Sandy','Maize', {'Moisture':38,'Nitrogen':37,'Potassium':0,'Phosphorous':0})")
