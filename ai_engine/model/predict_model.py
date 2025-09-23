import joblib
import pandas as pd
from datetime import datetime

from firebase.firebase_config import fetch_readings, save_prediction

# ---------------- Load Model ----------------
model_path = "model/oyster_growth_model.pkl"
model = joblib.load(model_path)
print(f"✅ Model loaded from {model_path}")

# ---------------- Fetch Latest Readings ----------------
print("📡 Fetching latest sensor readings from Firebase for prediction...")
readings = fetch_readings()
if not readings:
    print("❌ No readings available for prediction!")
    exit()

df = pd.DataFrame(readings)
df["temperature"] = df["temperature"].astype(float)
df["salinity"] = df["salinity"].astype(float)
df["turbidity"] = df["turbidity"].astype(float)
df["ph"] = df["ph"].astype(float)
df["do"] = df["do"].astype(float)

# ---------------- Predict ----------------
X_new = df[["temperature", "salinity", "turbidity", "ph", "do"]]
predictions = model.predict(X_new)

# ---------------- Save Predictions ----------------
for idx, row in df.iterrows():
    pred_record = {
        "temperature": row["temperature"],
        "salinity": row["salinity"],
        "turbidity": row["turbidity"],
        "ph": row["ph"],
        "do": row["do"],
        "timestamp": row.get("timestamp", datetime.utcnow().isoformat()),
        "predicted_growth": int(predictions[idx])
    }
    status_code, response_text = save_prediction(pred_record)
    print(f"✅ Prediction saved: {pred_record['predicted_growth']} | HTTP {status_code}")

print("\n✅ All predictions processed and saved to Firebase.")
