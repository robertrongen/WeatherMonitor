# reboot_notify.py

import os
import requests
from dotenv import load_dotenv
from app_logging import setup_logger

load_dotenv()
logger = setup_logger("reboot_notify", "reboot_notify.log")

STATE_FILE = "/var/run/reboot_reason"

def send_pushover(message, priority=0):
    token = os.getenv("PUSHOVER_API_TOKEN")
    user = os.getenv("PUSHOVER_USER_KEY")

    if not token or not user:
        logger.warning("Pushover credentials missing")
        return

    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": message,
                "priority": priority,
            },
            timeout=5,
        )
        logger.info(f"Pushover sent: {message}")
    except Exception as e:
        logger.error(f"Pushover failed: {e}")

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
