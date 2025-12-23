# reboot_notify.py

import os
import requests
from dotenv import load_dotenv
from app_logging import setup_logger

load_dotenv()
logger = setup_logger("reboot_notify", "reboot_notify.log")

STATE_FILE = "/home/robert/.run/reboot_reason"
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

def send_pushover(message, priority=0):
    token = os.getenv("PUSHOVER_API_TOKEN")
    user = os.getenv("PUSHOVER_USER_KEY")

    # Diagnostic: Log credential presence (not values)
    logger.info(f"Pushover credentials check: token={'present' if token else 'MISSING'}, user={'present' if user else 'MISSING'}")

    if not token or not user:
        logger.error("Pushover credentials missing - cannot send notification")
        return

    try:
        # Diagnostic: Log request details
        logger.info(f"Sending Pushover notification with priority={priority}")
        
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": message,
                "priority": priority,
            },
            timeout=5,
        )
        
        # Diagnostic: Log HTTP response
        logger.info(f"Pushover HTTP status: {response.status_code}")
        logger.info(f"Pushover response body: {response.text}")
        
        # Validate response
        if response.status_code == 200:
            logger.info(f"✅ Pushover sent successfully: {message[:50]}...")
        else:
            logger.error(f"❌ Pushover API returned error status {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout as e:
        logger.error(f"Pushover request timeout after 5s: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Pushover network error: {e}")
    except Exception as e:
        logger.error(f"Pushover unexpected error: {type(e).__name__}: {e}")

def pre_reboot(reason: str):
    # Prevent duplicates
    if os.path.exists(STATE_FILE):
        return

    with open(STATE_FILE, "w") as f:
        f.write(reason)

    send_pushover(
        f"⚠️ Skymonitor reboot triggered\nReason: {reason}",
        priority=1,
    )

def post_boot():
    if not os.path.exists(STATE_FILE):
        return

    with open(STATE_FILE) as f:
        reason = f.read().strip()

    send_pushover(
        f"✅ Skymonitor back online\nPrevious reboot reason: {reason}"
    )

    os.remove(STATE_FILE)
