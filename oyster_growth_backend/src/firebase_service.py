import os
import firebase_admin
from firebase_admin import credentials, db
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI()

# -------------------------------
# Firebase Initialization
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# FIX: Correct service account path (remove duplicate 'data')
SERVICE_ACCOUNT_PATH = os.path.join(
    BASE_DIR, "data", "trial-reading-firebase-adminsdk-fbsvc-f9f7fa88ac.json"
)

DATABASE_URL = "https://trial-reading-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
        logging.info("✅ Firebase initialized successfully.")
    except Exception as e:
        logging.error(f"❌ Firebase initialization failed: {e}")
else:
    logging.info("ℹ️ Firebase already initialized.")

# -------------------------------
# Save data to Firebase
# -------------------------------
def save_data_to_firebase(path, data):
    """
    Save data to Firebase Realtime Database.
    """
    try:
        ref = db.reference(path)
        if not isinstance(data, dict):
            logging.error("❌ Data must be a dictionary.")
            return False
        ref.push(data)
        logging.info(f"✅ Data saved to Firebase at '{path}': {data}")
        return True
    except Exception as e:
        logging.error(f"❌ Error saving data: {e}")
        return False

# -------------------------------
# Get latest data
# -------------------------------
def get_latest_data_from_firebase(path):
    try:
        ref = db.reference(path)
        snapshot = ref.order_by_key().limit_to_last(1).get()
        if snapshot:
            last_key = list(snapshot.keys())[0]
            return snapshot[last_key]
        else:
            return None
    except Exception as e:
        logging.error(f"❌ Error fetching latest data: {e}")
        return None

@app.post("/sensor-data")
async def receive_sensor_data(request: Request):
    try:
        body = await request.json()
        body["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = save_data_to_firebase("testmode3_live_readings", body)
        if success:
            return JSONResponse({"status": "success", "data": body})
        else:
            return JSONResponse({"status": "error", "message": "Failed to save to Firebase"})
    except Exception as e:
        logging.error(f"❌ Exception in /sensor-data: {e}")
        return JSONResponse({"status": "error", "message": str(e)})
