import sqlite3
from app_logging import setup_logger

logger = setup_logger('clear_database', 'database_operations.log')

def clear_sky_data():
    DATABASE_NAME = "sky_data.db"
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sky_data;")
        conn.commit()
        logger.info("All data cleared from sky_data table successfully.")
    except Exception as e:
        logger.error(f"Failed to clear data from sky_data table: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    clear_sky_data()
