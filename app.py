# app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
import os

app = Flask(__name__)
# Load initial settings from a JSON file or set default values
try:
    with open('settings.json', 'r') as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {
        "ambient_temp_threshold": 20,
        "cpu_temp_threshold": 65,
        "interval_time": 0.2,
        "sleep_time": 2,
        "temp_hum_url": 'https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1',
        "serial_port": '/dev/ttyUSB0',
        "baud_rate": 115200
    }

def get_db_connection():
    conn = sqlite3.connect('sky_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM sky_data ORDER BY timestamp DESC').fetchall()
        # Convert rows to list of dicts to ensure JSON serializability
        rows_list = [dict(row) for row in rows]
        timestamps = [row['timestamp'] for row in rows_list]  # Extracting timestamps as normal
    finally:
        conn.close()

    return render_template('index.html', data=rows_list, timestamps=json.dumps(timestamps))

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if request.method == 'POST':
        # Update settings based on form data
        settings['ambient_temp_threshold'] = int(request.form['ambient_temp_threshold'])
        settings['cpu_temp_threshold'] = int(request.form['cpu_temp_threshold'])
        settings['interval_time'] = float(request.form['interval_time'])
        settings['sleep_time'] = int(request.form['sleep_time'])
        settings['temp_hum_url'] = request.form['temp_hum_url']
        settings['serial_port'] = request.form['serial_port']
        settings['baud_rate'] = int(request.form['baud_rate'])
        
        # Save updated settings to a file
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)

        return redirect(url_for('settings_page'))
    else:
        return render_template('settings.html', settings=settings)

@app.route('/test')
def index_test():
    try:
        rows = [
            {'timestamp': '2021-01-01', 'cloud_coverage_indicator': 10},
            {'timestamp': '2021-01-02', 'cloud_coverage_indicator': 20},
        ]
        timestamps = [row['timestamp'] for row in rows]
    except Exception as e:
        rows = []
        timestamps = []
        print(f"Error fetching data: {e}")
    return render_template('index_test.html', data=rows, timestamps=json.dumps(timestamps))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
