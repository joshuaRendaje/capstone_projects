import os
import pandas as pd
import joblib
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# === CONFIGURATION ===
MODEL_PATH = os.path.join("model", "oyster_growth_model.pkl")
DATASET_FOLDER = "dataset"
PREDICTION_NODE = "predictions"
SERVICE_ACCOUNT_PATH = r"C:\Users\admin\oyster_ai_system\oyster_growth_backend\data\finalproject101-9d3ff-firebase-adminsdk-fbsvc-f782f6faf4.json"
DATABASE_URL = "https://finalproject101-9d3ff-default-rtdb.asia-southeast1.firebasedatabase.app/"

FEATURE_COLUMNS = [
    'temperature_C',
    'salinity_ppt',
    'turbidity_NTU',
    'dissolved_oxygen_mgL',
    'ph_level'
]

# === INITIALIZE FIREBASE ===
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        print("Konektado sa Firebase Realtime Database.")

# === LOAD MODEL ===
def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model hindi nakita sa {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print("Na-load ang trained model.")
    return model

# === GET LATEST DATASET ===
def get_latest_dataset():
    all_files = [f for f in os.listdir(DATASET_FOLDER) if f.endswith(".csv")]
    if not all_files:
        print("Walang dataset files sa folder.")
        return None
    all_files.sort(key=lambda x: os.path.getmtime(os.path.join(DATASET_FOLDER, x)), reverse=True)
    latest_file = os.path.join(DATASET_FOLDER, all_files[0])
    print(f"Ginagamit ang pinakabagong dataset: {latest_file}")
    return latest_file

# === COMPUTE ADAPTIVE THRESHOLDS ===
def compute_adaptive_thresholds():
    all_files = [os.path.join(DATASET_FOLDER, f) for f in os.listdir(DATASET_FOLDER) if f.endswith(".csv")]
    if not all_files:
        print("Walang historical dataset para sa adaptive thresholds.")
        return None

    df_list = [pd.read_csv(f) for f in all_files]
    historical_df = pd.concat(df_list, ignore_index=True)

    thresholds = {}
    for col in FEATURE_COLUMNS:
        lower = historical_df[col].quantile(0.1)
        upper = historical_df[col].quantile(0.9)
        thresholds[col] = (lower, upper)

    print("Adaptive thresholds computed:")
    for k, v in thresholds.items():
        print(f"{k}: {v[0]:.2f} – {v[1]:.2f}")
    return thresholds

# === MAKE PREDICTIONS WITH ADAPTIVE THRESHOLDS ===
def make_predictions(model, dataset_file, thresholds):
    df = pd.read_csv(dataset_file)
    df = df.dropna(subset=FEATURE_COLUMNS)
    if df.empty:
        print("Walang valid rows para mag-predict.")
        return None

    X = df[FEATURE_COLUMNS]
    pred_labels = model.predict(X)
    df['prediction'] = pred_labels

    # APPLY ADAPTIVE THRESHOLDS
    def adaptive_check(row):
        for col in FEATURE_COLUMNS:
            lower, upper = thresholds[col]
            if row[col] < lower or row[col] > upper:
                return "bad_for_harvest"
        return row['prediction']

    df['prediction'] = df.apply(adaptive_check, axis=1)
    return df

# === SAVE AND PUSH PREDICTIONS ===
def save_and_push_predictions(df):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(DATASET_FOLDER, exist_ok=True)
    csv_path = os.path.join(DATASET_FOLDER, f"predictions_{timestamp}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Predictions na-save locally sa: {csv_path}")

    init_firebase()
    ref = db.reference(PREDICTION_NODE)
    for _, row in df.iterrows():
        safe_row = {k: float(v) if isinstance(v, (int, float)) else str(v) for k, v in row.items()}
        ref.push(safe_row)
    print("Predictions na-push sa Firebase.")

# === MAIN FUNCTION ===
def predict():
    model = load_model()
    latest_file = get_latest_dataset()
    if not latest_file:
        return

    thresholds = compute_adaptive_thresholds()
    if thresholds is None:
        return

    df_predictions = make_predictions(model, latest_file, thresholds)
    if df_predictions is None:
        return

    print("Sample predictions:")
    print(df_predictions.head())
    save_and_push_predictions(df_predictions)

if __name__ == "__main__":
    predict()
