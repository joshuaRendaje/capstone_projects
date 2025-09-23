# === Install if needed ===
# pip install lightgbm scikit-learn pandas joblib

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from lightgbm import LGBMClassifier
import joblib

# === 1. Load dataset ===
df = pd.read_csv("oyster_large_dataset.csv")  # use the generated 50k+ dataset

# === 2. Select features & target ===
features = [
    "Temperature (°C)",
    "Salinity (ppt)",
    "pH",
    "Dissolved Oxygen (mg/L)",
    "Oyster Count",
    "Growth Rate (%)"
]
target = "Health_Status"  # Healthy, At Risk, Critical

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
    class_weight="balanced"  # handle imbalanced classes
)
model.fit(X_train, y_train)

# === 5. Evaluate ===
y_pred = model.predict(X_test)
print("Classification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# === 6. Save model ===
joblib.dump(model, "predict_water_quality_2025.pkl")
print("✅ Model saved as predict_water_quality_2025.pkl")

# === 7. Example prediction ===
sample = pd.DataFrame([{
    "Temperature (°C)": 27.5,
    "Salinity (ppt)": 30.2,
    "pH": 7.7,
    "Dissolved Oxygen (mg/L)": 6.2,
    "Oyster Count": 520,
    "Growth Rate (%)": 2.1
}])

pred = model.predict(sample)[0]
print("Sample Prediction:", pred)
