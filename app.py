# app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
import os
import pytz
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('sky_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def utc_to_cet(utc_str):
    utc_zone = pytz.utc
    cet_zone = pytz.timezone('Europe/Berlin')  # Berlin timezone covers both CET and CEST
    utc_dt = datetime.strptime(utc_str, '%Y-%m-%d %H:%M:%S')
    cet_dt = utc_zone.localize(utc_dt).astimezone(cet_zone)
    return cet_dt.strftime('%Y-%m-%d %H:%M:%S')

def read_log_file(path):
    try:
        with open(path, 'r') as file:
            return file.readlines()  # Return the lines in the file
    except IOError:
        return ["Unable to read file, please check the file path and permissions."]

@app.route('/')
def index():
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM sky_data ORDER BY timestamp DESC').fetchall()
        # Convert rows to list of dicts to ensure JSON serializability
        rows_list = [dict(row) for row in rows]
        # timestamps = [row['timestamp'] for row in rows_list]  # Extracting timestamps as normal
        # Convert UTC timestamps to CET/CEST for display
        for row in rows_list:
            row['timestamp'] = utc_to_cet(row['timestamp'])
    finally:
        conn.close()

    # return render_template('index.html', data=rows_list, timestamps=json.dumps(timestamps))
    return render_template('index.html', data=rows_list)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html'), logwatch_report_url="/etc/logwatch/report/logwatch.html")

@app.route('/data')
def serial_data():
    conn = sqlite3.connect('sky_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1440')  # Last 24 hours if data is logged every minute
    data = c.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

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

@app.route('/logs/<string:log_name>')
def show_logs(log_name):
    log_path = {
        'syslog': '/var/log/syslog',
        'messages': '/var/log/messages'
    }.get(log_name)

    if log_path and os.access(log_path, os.R_OK):
        logs = read_log_file(log_path)
        return render_template('logs.html', logs=logs, log_name=log_name)
    else:
        abort(403)  # Abort if the log path is not recognized or not readable

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
