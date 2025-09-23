import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from datetime import datetime, timedelta

from firebase.firebase_config import fetch_readings

# ---------------- Fetch Firebase Data ----------------
print("📡 Fetching sensor readings from Firebase...")
data = fetch_readings()
if not data:
    raise ValueError("❌ No sensor readings found in Firebase!")

df = pd.DataFrame(data)
print(f"✅ Dataset loaded from Firebase: {df.shape}")
print(df.head())

# ---------------- Preprocess Data ----------------
df["temperature"] = df["temperature"].astype(float)
df["salinity"] = df["salinity"].astype(float)
df["turbidity"] = df["turbidity"].astype(float)
df["ph"] = df["ph"].astype(float)
df["do"] = df["do"].astype(float)

# ---------------- Define Growth Label ----------------
def label_growth(row):
    """Label sensor readings as 1 (Good) or 0 (Bad)"""
    if (
        25 <= row["salinity"] <= 32 and
        20 <= row["temperature"] <= 28 and
        7.8 <= row["ph"] <= 8.2 and
        row["turbidity"] <= 8 and
        row["do"] >= 5
    ):
        return 1
    return 0

df["growth_status"] = df.apply(label_growth, axis=1)

# ---------------- Features & Target ----------------
X = df[["temperature", "salinity", "turbidity", "ph", "do"]]
y = df["growth_status"]

# ---------------- Train/Test Split ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------------- Train Model ----------------
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# ---------------- Evaluate ----------------
y_pred = model.predict(X_test)
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# ---------------- Save Model ----------------
model_dir = os.path.join(os.path.dirname(__file__), "model")
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "oyster_growth_model.pkl")
joblib.dump(model, model_path)
print(f"\n✅ Model saved to {model_path}")
