from fastapi import FastAPI
from datetime import datetime
import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

from firebase.firebase_config import fetch_readings, save_prediction

# ---------------- FastAPI App ----------------
app = FastAPI(title="Oyster AI Train & Predict API", version="1.0.0")

# ---------------- Model Path ----------------
MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "oyster_growth_model.pkl")
os.makedirs(MODEL_DIR, exist_ok=True)

# ---------------- Helper Function ----------------
def label_growth(row):
    """Label sensor readings as Good(1) or Bad(0)."""
    if (
        25 <= row["salinity"] <= 32 and
        20 <= row["temperature"] <= 28 and
        7.8 <= row["ph"] <= 8.2 and
        row["turbidity"] <= 8 and
        row["do"] >= 5
    ):
        return 1
    return 0

# ---------------- Endpoint ----------------
@app.get("/train_predict")
def train_and_predict():
    # Fetch readings
    readings = fetch_readings()
    if not readings:
        return {"status": "error", "message": "No sensor readings found in Firebase."}

    df = pd.DataFrame(readings)
    df["temperature"] = df["temperature"].astype(float)
    df["salinity"] = df["salinity"].astype(float)
    df["turbidity"] = df["turbidity"].astype(float)
    df["ph"] = df["ph"].astype(float)
    df["do"] = df["do"].astype(float)

    # Label growth
    df["growth_status"] = df.apply(label_growth, axis=1)

    # Features & target
    X = df[["temperature", "salinity", "turbidity", "ph", "do"]]
    y = df["growth_status"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, zero_division=0, output_dict=True)

    # Save model
    joblib.dump(model, MODEL_PATH)

    # ---------------- Predict for all readings ----------------
    predictions = model.predict(X)
    saved_predictions = []

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
        saved_predictions.append({
            "predicted_growth": int(predictions[idx]),
            "status_code": status_code
        })

    return {
        "status": "success",
        "message": "Model trained and predictions saved to Firebase.",
        "model_path": MODEL_PATH,
        "classification_report": report,
        "total_predictions_saved": len(saved_predictions)
    }
