# === Install if needed ===
# pip install lightgbm scikit-learn pandas joblib

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from lightgbm import LGBMClassifier
import joblib

# === 1. Load dataset ===
df = pd.read_pickle("sample_oyster_dataset.pkl")

# === 2. Select features & target ===
features = [
    "pH", "temperature_C", "turbidity_NTU", "dissolved_oxygen_mgL", "salinity_PSU",
    "rainfall_24h_mm", "wind_speed_mps", "solar_Wm2", "tide_m"
]
target = "oyster_status"  # matches our dataset ("NORMAL"/"WARNING")

X = df[features]
y = df[target]

# === 3. Train-test split ===
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=True, random_state=42, stratify=y
)

# === 4. Train model ===
model = LGBMClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=-1,
    random_state=42,
    class_weight="balanced"  # fair handling of NORMAL vs WARNING
)
model.fit(X_train, y_train)

# === 5. Evaluate ===
y_pred = model.predict(X_test)
print("Classification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# === 6. Save model ===
joblib.dump(model, "blank1_sensors_model.pkl")
print("✅ Model saved as sample1_risk_model.pkl")

# === 7. Example prediction ===
sample = pd.DataFrame([{
    "pH": 7.9,
    "temperature_C": 29,
    "turbidity_NTU": 12,
    "dissolved_oxygen_mgL": 6.8,
    "salinity_PSU": 31,
    "rainfall_24h_mm": 3,
    "wind_speed_mps": 4,
    "solar_Wm2": 820,
    "tide_m": 0.4
}])

pred = model.predict(sample)[0]
print("Sample Prediction:", pred)
