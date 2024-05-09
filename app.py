# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
from flask_socketio import SocketIO, emit
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
socketio = SocketIO(app)

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

def get_latest_data():
    """Retrieve the latest data from the database."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM sky_data ORDER BY timestamp DESC LIMIT 25')
        rows = c.fetchall()
        # Convert rows to list of dicts to ensure JSON serializability
        rows_list = [dict(row) for row in rows]
        # Convert UTC timestamps to CET/CEST for display
        for row in rows_list:
            row['timestamp'] = utc_to_cet(row['timestamp'])
        return rows_list 
    except Exception as e:
        print(f"Error fetching or converting data: {e}")
        return []
    finally:
        conn.close()

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
    rows_list = get_latest_data()
    if rows_list:
        return render_template('index.html', data=rows_list, alert_active=alert_active)
    else:
        return jsonify({"error": "Error fetching rows_list"}), 500

@app.route('/data')
def serial_data():
    """API endpoint to fetch data."""
    data = get_latest_data()
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "Error fetching data"}), 500

@app.route('/load-more')
def load_more():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM sky_data ORDER BY timestamp DESC LIMIT 100 OFFSET 10')  # Adjust OFFSET based on initial data load
    data = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(data)

def notify_new_data():
    """Function to emit new data to all connected clients."""
    data = get_latest_data()
    if data:
        print("Emitting new data: ", data)  # Debug log
        socketio.emit('new_data', {'data': data})
        # socketio.emit('new_data', {'data': data}, namespace='/data')
    else:
        print("Error: No data available to send.")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', allow_unsafe_werkzeug=True)
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

        # For string values (no type conversion needed)
        settings['temp_hum_url'] = request.form.get('temp_hum_url', settings['temp_hum_url'])
        settings['serial_port_rain'] = request.form.get('serial_port_rain', settings['serial_port_rain'])
        settings['serial_port_json'] = request.form.get('serial_port_json', settings['serial_port_json'])

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

@socketio.on('connect')
def test_connect():
    app.logger.info('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    app.logger.info('Client disconnected')

