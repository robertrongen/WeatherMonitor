# store_data.py
# === DEPRECATED ===
# This module is deprecated as of the HTTP-only refactor.
# Historical data storage has been removed to reduce disk I/O.
# Only the last known good snapshot is retained in state.json.
#
# This file is kept for backward compatibility only.
# All functions are now stubs that do nothing.
# ===================

import sqlite3
from datetime import datetime
from app_logging import setup_logger
import warnings

warnings.warn("store_data.py is deprecated and will be removed in a future release", DeprecationWarning, stacklevel=2)

logger = setup_logger('store_data', 'store_data.log')

DATABASE_NAME = "sky_data.db"

def setup_database(conn=None):
    """DEPRECATED: No-op stub - database storage removed"""
    logger.warning("setup_database() called but is deprecated - no action taken")
    pass

def store_sky_data(data, conn=None):
    """DEPRECATED: No-op stub - database storage removed"""
    # Silently ignore - this may be called by legacy code
    pass

if __name__ == "__main__":
    print("store_data.py is deprecated - database storage has been removed")
    print("State is now maintained in memory by control.py")
