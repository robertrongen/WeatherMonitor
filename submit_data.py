# submit_data.py

from flask import Flask, render_template, jsonify, request, redirect, url_for
from zeroconf import ServiceInfo, Zeroconf, NonUniqueNameException
import socket
import atexit
import sqlite3
import os

app = Flask(__name__)

DATABASE_NAME = "weather_data.db"

def format_float(value):
    if value is None:
        return "N/A"  # or any other default value you'd like to display for None values
    try:
        return "{:.2f}".format(float(value))
    except ValueError:
        return value

app.jinja_env.filters['format_float'] = format_float

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    show_all = 'show_all' in request.args
    message = request.args.get('message')
    
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        if show_all:
            cursor.execute("SELECT timestamp, cloud_coverage_indicator, brightness FROM weather_data")
        else:
            cursor.execute("SELECT timestamp, cloud_coverage_indicator, brightness FROM weather_data WHERE timestamp >= datetime('now', '-1 day')")
        
        data = cursor.fetchall()
        
        cursor.execute("SELECT * FROM weather_data ORDER BY timestamp DESC LIMIT 5")
        last_data_list = cursor.fetchall()
        # Handle missing values in the fetched data
        processed_data_list = []
        for row in last_data_list:
            processed_row = tuple(value if value is not None else 'N/A' for value in row)
            processed_data_list.append(processed_row)

        print(processed_data_list)

    if data:
        timestamps, cloud_coverage_indicators, brightnesses = zip(*data)
    else:
        timestamps, cloud_coverage_indicators, brightnesses = [], [], []

    return render_template('index.html', 
        timestamps=timestamps, 
        cloud_coverage_indicators=cloud_coverage_indicators, 
        brightnesses=brightnesses,
        last_data=processed_data_list,
        message=message,
        show_all=show_all
    )

@app.route('/submit_observation', methods=['POST'])
def submit_observation():
    cloud_condition = request.form['cloud_condition']
    rain_condition = request.form['rain_condition']
    moon_visibility = request.form['moon_visibility']

    # Fetch the most recent record from the weather_data table
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM weather_data ORDER BY timestamp DESC LIMIT 1")
        current_data = cursor.fetchone()

        # Insert the observation along with the current weather data into the observations table
        cursor.execute("""
            INSERT INTO observations (cloud_condition, rain_condition, moon_visibility, temperature, sky_temperature, cloud_coverage_indicator, sqm_lux, brightness, bortle)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cloud_condition, rain_condition, moon_visibility, current_data[1], current_data[2], current_data[3], current_data[4], current_data[5], current_data[6]))

    return redirect(url_for('index', message='Submitted'))

@app.route('/observations')
def observations():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM observations ORDER BY timestamp DESC")
        observations_data = cursor.fetchall()

    return render_template('observations.html', observations=observations_data)

@app.route('/api/v1/cloudcoverage', methods=['GET'])
def get_cloud_coverage():
    # Fetch the latest cloud coverage indicator from the database
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cloud_coverage_indicator FROM weather_data ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()

    if result:
        cloud_coverage_indicator = result[0]
        response = {
            "Value": cloud_coverage_indicator,
            "Status": 0  # 0 indicates no error
        }
    else:
        response = {
            "Value": None,
            "Status": 1  # 1 indicates an error or no data available
        }

    return jsonify(response)

def register_mdns_service():
    ip_address = socket.gethostbyname(socket.gethostname())
    service_name = "SkyMonitor._http._tcp.local."
    service_port = 5000
    service_type = "_http._tcp.local."
    service_properties = {"path": "/"}
    
    info = ServiceInfo(
        type_=service_type,
        name=service_name,
        addresses=[socket.inet_aton(ip_address)],
        port=service_port,
        properties=service_properties,
        server=f"sky.local.",
    )

    zeroconf = Zeroconf()

    try:
        # Now register the service
        zeroconf.register_service(info)
    except NonUniqueNameException:
        print("Service name already in use. Please ensure no other instances are running or change the service name.")
        # Optionally, you can change the service name here and try registering again.
        # service_name = "SkyMonitorUnique._http._tcp.local."
        # ... (rest of the code to create a new ServiceInfo and register it)
    return zeroconf

if __name__ == '__main__':
    cert_path = os.path.expanduser('~/.ssh/cert.pem')
    key_path = os.path.expanduser('~/.ssh/key.pem')
    zeroconf_instance = register_mdns_service()
    app.run(debug=True, host='0.0.0.0', ssl_context=(cert_path, key_path))
    zeroconf_instance.close()  # Close the Zeroconf instance when Flask stops
