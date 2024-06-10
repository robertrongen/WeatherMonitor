# Skymonitor Project

## Installation

### Add .env Variables
Create and fill in `.env` keys using `example.env` for:
- OpenWeatherMap API and app keys (https://openweathermap.org/api)
- `SESSION_KEY`: Create a web session key:
  ```bash
  python -c 'import os; print(os.urandom(24).hex())'
  ```

### Activate Virtual Environment for Python (venv)
1. Create a new virtual environment:
   ```bash
   python3 -m venv venv
   ```
2. Activate the new environment:
   ```bash
   source venv/bin/activate
   ```
3. Install pip:
   ```bash
   wget https://bootstrap.pypa.io/get-pip.py
   python get-pip.py
   ```
4. Reinstall all your packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Update requirements after installing new packages:
   ```bash
   pipreqs
   ```
6. Deactivate the current environment:
   ```bash
   deactivate
   ```
7. Remove the current virtual environment folder:
   ```bash
   rm -r venv
   ```

## Define Services

### For `app.py` - Runs Flask Webserver for `/` and `/settings` with DNS to `skymonitor.local`
### For `control.py` - Manages `control_fan_heater()`, gets and stores sensor data according to schedule, controls fan and dew heater, and calls `rain_alarm`

1. Create the service:
   ```bash
   sudo nano /etc/systemd/system/app.service
   ```
2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```
3. Enable the service:
   ```bash
   sudo systemctl enable app.service
   ```
4. Start the service:
   ```bash
   sudo systemctl start app.service
   ```
5. Check status:
   ```bash
   sudo systemctl status app.service
   ```

Service file content for `app.service`:
```
[Unit]
Description=Skymonitor App Service
After=network.target

[Service]
Type=simple
User=robert
WorkingDirectory=/home/user/skymonitor
ExecStart=/home/user/skymonitor/venv/bin/python /home/user/skymonitor/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

Service file content for `control.service`:
```
[Unit]
Description=Skymonitor Control Service
After=network.target

[Service]
Type=simple
User=robert
WorkingDirectory=/home/user/skymonitor
ExecStart=/home/user/skymonitor/venv/bin/python /home/user/skymonitor/control.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

## Operation

### Code Update Procedure

On RPi:
1. Commit and push "settings.json" from RPi:
   ```bash
   git commit -a
   git push
   ```

On development laptop:
2. Update and test code.
3. Commit and push the updates:
   ```bash
   git commit -a
   git push
   ```

On RPi:
4. Pull the updates:
   ```bash
   git pull
   ```
5. Restart the services:
   ```bash
   sudo systemctl restart app
   sudo systemctl restart control
   ```

### Testing and Bug Fixing

#### On Development Laptop:
- Use `python3 serial_test_data.py` to generate serial data and follow port setting instructions.

#### On RPi (Remote Session):
1. Activate venv:
   ```bash
   source ~/github/skymonitor/venv/bin/activate
   ```

2. Configure Geany to use the virtual environment’s interpreter:
   - Open Geany, navigate to Build → Set Build Commands.
   - Under the Execute commands, modify the command line to use the Python interpreter from your virtual environment:
     ```bash
     ~/github/skymonitor/venv/bin/python "%f"
     ```

3. Check log files using:
   ```bash
   cat control.log
   ```
   Log files to check:
   - `control.log`
   - `app.log`
   - `fetch_data.log`
   - `store_data.log`
   - `database_operations.log`
   - `rain.log`

4. Check journal:
   ```bash
   sudo journalctl -u control.service -S today
   sudo journalctl -u app.service -S today
   ```

5. Reset logs and journals:
   ```bash
   ./admin/reset_logs.sh
   ```

## System Monitoring

A separate service is used to collect and store system metrics like CPU temperature, CPU usage, memory usage, and disk usage.
Manually check system with `htop` or check <http://allsky.local/index.php?page=system>

### Setting Up System Monitor Service

1. Create the service:
   ```bash
   sudo nano /etc/systemd/system/system_monitor.service
   ```
2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```
3. Enable the service:
   ```bash
   sudo systemctl enable system_monitor.service
   ```
4. Start the service:
   ```bash
   sudo systemctl start system_monitor.service
   ```
5. Check status:
   ```bash
   sudo systemctl status system_monitor.service
   ```

Service file content for `system_monitor.service`:
```
[Unit]
Description=System Monitor Service
After=network.target

[Service]
Type=simple
User=robert
WorkingDirectory=/home/user/skymonitor
ExecStart=/home/user/skymonitor/venv/bin/python /home/user/skymonitor/system_monitor.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

## API Endpoints

### Sky Data
- URL: `/api/sky_data`
- Method: GET
- Description: Fetches the latest entries from the `sky_data` table.

### Metrics Data
- URL: `/api/metrics_data`
- Method: GET
- Description: Fetches the latest entries from the `Metrics` table.

### Testing the API
1. Start your Flask application:
   ```bash
   python app.py
   ```

2. Access the API endpoints:
   - Fetch latest sky data: `http://<your_server_ip>:<port>/api/sky_data`
   - Fetch latest metrics data: `http://<your_server_ip>:<port>/api/metrics_data`

These endpoints return the latest data from the respective tables in JSON format.