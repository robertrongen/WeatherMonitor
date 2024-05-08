# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
import sqlite3
import json
import os
import pytz
from dotenv import load_dotenv
from datetime import datetime, timedelta
from settings import load_settings

app = Flask(__name__)

load_dotenv()
app.secret_key = os.getenv('SESSION_KEY')
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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

# Global variable to store the alert state
alert_active = False

@app.route('/enable-alert', methods=['POST'])
def enable_alert():
    global alert_active
    alert_active = True
    return redirect(url_for('index'))

@app.route('/disable-alert', methods=['POST'])
def disable_alert():
    global alert_active
    alert_active = False
    return redirect(url_for('index'))

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
    return render_template('index.html', data=rows_list, alert_active=alert_active)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    settings = load_settings()

    if request.method == 'POST':
        # Update settings based on form data
        # For integer values
        settings['raining_threshold'] = int(request.form.get('raining_threshold', settings['raining_threshold']))
        settings['ambient_temp_threshold'] = int(request.form.get('ambient_temp_threshold', settings['ambient_temp_threshold']))
        settings['dewpoint_threshold'] = int(request.form.get('dewpoint_threshold', settings['dewpoint_threshold']))
        settings['cpu_temp_threshold'] = int(request.form.get('cpu_temp_threshold', settings['cpu_temp_threshold']))
        settings['memory_usage_threshold'] = int(request.form.get('memory_usage_threshold', settings['memory_usage_threshold']))
        settings['sleep_time'] = int(request.form.get('sleep_time', settings['sleep_time']))
        settings['baud_rate'] = int(request.form.get('baud_rate', settings['baud_rate']))

        # For floating point value
        settings['interval_time'] = float(request.form.get('interval_time', settings['interval_time']))

        # For string values (no type conversion needed)
        settings['temp_hum_url'] = request.form.get('temp_hum_url', settings['temp_hum_url'])
        settings['serial_port'] = request.form.get('serial_port', settings['serial_port'])

        # Save updated settings to a file
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)

        flash('Settings have been updated successfully!', 'success')  # Flash a success message
        return redirect(url_for('settings_page'))
    else:
        return render_template('settings.html', settings=settings)
        
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', logwatch_report_url='/etc/logwatch/report/logwatch.html')

@app.route('/data')
def serial_data():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 25')
        rows = c.fetchall()
        print("Fetched rows:", rows)  # Debug print to check what's being fetched
        
        # Convert rows to dictionaries if row factory is set correctly
        data = [dict(row) for row in rows]
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching or converting data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/load-more')
def load_more():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 100 OFFSET 10')  # Adjust OFFSET based on initial data load
    data = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(data)

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
