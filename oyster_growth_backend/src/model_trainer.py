import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from firebase_admin import credentials, db
import firebase_admin
from datetime import datetime

# === CONFIGURATION ===
MODEL_PATH = os.path.join("model", "oyster_growth_model.pkl")
DATASET_FOLDER = "dataset"
SERVICE_ACCOUNT_PATH = r"C:\Users\admin\oyster_ai_system\oyster_growth_backend\data\finalproject101-9d3ff-firebase-adminsdk-fbsvc-f782f6faf4.json"
DATABASE_URL = "https://finalproject101-9d3ff-default-rtdb.asia-southeast1.firebasedatabase.app/"
LIVE_NODE = "new_live_readings"
PREDICTION_NODE = "new_live_predictions"

FEATURE_COLUMNS = [
    'temperature_C',
    'salinity_ppt',
    'turbidity_NTU',
    'dissolved_oxygen_mgL',
    'ph_level'
]

# === FIREBASE INITIALIZATION ===
def init_firebase():
    if not firebase_admin._apps:  # check kung initialized na
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        print("Connected to Firebase Realtime Database.")

# === LOAD MODEL ===
def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print("Loaded model.")
    return model

# === FETCH NEW SENSOR DATA ===
def fetch_new_data():
    init_firebase()
    ref = db.reference(LIVE_NODE)
    data = ref.get()
    if not data:
        print("No live data found.")
        return None
    df = pd.DataFrame(data.values())
    df = df.dropna(subset=FEATURE_COLUMNS)
    return df

# === COMPUTE ADAPTIVE THRESHOLDS ===
def compute_adaptive_thresholds():
    all_files = [os.path.join(DATASET_FOLDER, f) for f in os.listdir(DATASET_FOLDER) if f.endswith(".pkl")]
    if not all_files:
        print("No historical datasets found for adaptive thresholds.")
        return None

    df_list = []
    for f in all_files:
        df = pd.read_csv(f)
        df_list.append(df)
    historical_df = pd.concat(df_list, ignore_index=True)

    thresholds = {}
    for col in FEATURE_COLUMNS:
        lower = historical_df[col].quantile(0.1)  # 10th percentile
        upper = historical_df[col].quantile(0.9)  # 90th percentile
        thresholds[col] = (lower, upper)

    print("Adaptive thresholds computed:")
    for k, v in thresholds.items():
        print(f"{k}: {v[0]:.2f} – {v[1]:.2f}")
    return thresholds

# === APPLY ADAPTIVE PREDICTION ===
def apply_adaptive_prediction(df, thresholds):
    def classify(row):
        for col in FEATURE_COLUMNS:
            lower, upper = thresholds[col]
            if row[col] < lower or row[col] > upper:
                return "bad_for_harvest"
        return "good_for_harvest"

    df['prediction'] = df.apply(classify, axis=1)
    return df

# === SAVE AND PUSH PREDICTIONS ===
def save_and_push_predictions(df):
    os.makedirs(DATASET_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(DATASET_FOLDER, f"predictions_{timestamp}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Predictions saved locally at {csv_path}")

    init_firebase()
    firebase_ref = db.reference(PREDICTION_NODE)
    for _, row in df.iterrows():
        firebase_ref.push(row.to_dict())
    print("Predictions success now pushed to Firebase.")

# === MAIN FUNCTION ===
def predict():
    model = load_model()
    df = fetch_new_data()
    if df is None or df.empty:
        print("No valid new data to predict.")
        return

    thresholds = compute_adaptive_thresholds()
    if thresholds is None:
        print("Cannot compute adaptive thresholds. Exiting.")
        return

    df = apply_adaptive_prediction(df, thresholds)
    print("Sample predictions:")
    print(df.head())

    save_and_push_predictions(df)

if __name__ == "__main__":
    predict()
