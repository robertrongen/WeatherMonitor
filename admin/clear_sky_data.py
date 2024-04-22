# clear_sky_data.py
import os
import sqlite3
from getpass import getpass
from dotenv import load_dotenv

load_dotenv()

DATABASE_NAME = "../sky_data.db"
SECRET_CODE = os.getenv('SECRET_CODE', 'default_secret_code')

def clear_sky_data():
    secret_code = getpass("Enter the secret code to proceed: ")

    if secret_code != SECRET_CODE:
        print("Incorrect secret code. Exiting without clearing the database.")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM sky_data")
        conn.commit()
        print("All data has been successfully cleared from the database.")
    except sqlite3.Error as e:
        print(f"An error occurred while trying to clear the database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clear_sky_data()
