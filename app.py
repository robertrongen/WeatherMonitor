# app.py
from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('sky_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM sky_data ORDER BY timestamp DESC').fetchall()
    timestamps = [row['timestamp'] for row in rows]  # Assuming 'timestamp' is a column in your 'sky_data'
    conn.close()
    return render_template('index.html', data=rows, timestamps=timestamps)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
