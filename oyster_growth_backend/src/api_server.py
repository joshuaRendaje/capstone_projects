from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import firebase_admin
from firebase_admin import credentials, db
import os
from datetime import datetime
import logging

# ==================================
# FIREBASE INITIALIZATION
# ==================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# FIX: Remove duplicate 'data' in service account path
SERVICE_ACCOUNT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../data/trial-reading-firebase-adminsdk-fbsvc-f9f7fa88ac.json"))

DATABASE_URL = "https://trial-reading-default-rtdb.europe-west1.firebasedatabase.app/"

# FIX: Ensure Firebase is initialized before any db.reference calls
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
        logging.info("✅ Firebase initialized successfully.")
    except Exception as e:
        logging.error(f"❌ Firebase initialization failed: {e}")
else:
    logging.info("ℹ️ Firebase already initialized.")

# ==================================
# FASTAPI APP
# ==================================
app = FastAPI()

def save_data_to_firebase(path, data):
    try:
        # FIX: Check if Firebase is initialized before saving
        if not firebase_admin._apps:
            logging.error("❌ Firebase app not initialized.")
            return False
        ref = db.reference(path)
        if not isinstance(data, dict):
            logging.error("❌ Data must be a dictionary.")
            return False
        result = ref.push(data)
        logging.info(f"✅ Data saved to Firebase at '{path}': {data} | Key: {result.key}")
        return True
    except Exception as e:
        logging.error(f"❌ Error saving data: {e}")
        return False

@app.post("/sensor-data")
async def receive_sensor_data(request: Request):
    try:
        body = await request.json()
        body["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = save_data_to_firebase("trial1_Reading", body)
        if success:
            return JSONResponse({"status": "success", "data": body})
        else:
            return JSONResponse({"status": "error", "message": "Failed to save to Firebase"})
    except Exception as e:
        logging.error(f"❌ Exception in /sensor-data: {e}")
        return JSONResponse({"status": "error", "message": str(e)})

@app.get("/latest-reading")
def get_latest_reading():
    try:
        ref = db.reference("trial1_Reading")
        data = ref.get()

        if not data:
            return {"message": "No readings found"}

        # Get latest entry based on timestamp
        readings = list(data.values())
        readings.sort(key=lambda x: x.get("timestamp", ""))
        latest = readings[-1]
        return latest

    except Exception as e:
        return {"error": str(e)}

@app.get("/all-readings")
def get_all_readings():
    try:
        ref = db.reference("trial1_Reading")
        data = ref.get()
        # Convert Firebase dict to list of readings sorted by timestamp if available
        if data:
            readings = list(data.values())
            # Optional: sort by timestamp if present
            readings.sort(key=lambda x: x.get("timestamp", ""))
            return readings
        else:
            return []
    except Exception as e:
        logging.error(f"❌ Error fetching readings: {e}")
        return []

if __name__ == "__main__":
    # FIX: Use relative path for module when running directly
    uvicorn.run("src.api_server:app", host="0.0.0.0", port=8000, reload=True)


#  uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload