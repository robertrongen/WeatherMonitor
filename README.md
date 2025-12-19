# AllSky Safety Monitor

**Raspberry Pi observatory safety system with environmental sensors**

## Project Structure

```
skymonitor/
├─ safety-monitor/          # Raspberry Pi Python application
├─ firmware/
│  ├─ allsky-sensors/       # Heltec WiFi LoRa 32 V2 sensor node
│  ├─ legacy/               # Archived Arduino+ESP8266 USB serial firmware
│  └─ display-client/       # LILYGO T-Display client
├─ docs/
│  ├─ architecture/
│  │  ├─ board-esp32-lora-display/  # Board #4 specifications (CANONICAL)
│  │  ├─ legacy/                     # Superseded designs
│  │  └─ ARCHITECTURE_PLAN_V2.md    # Current system architecture
│  ├─ governance/                    # Project management
│  │  ├─ REPOSITORY_GOVERNANCE.md
│  │  └─ INTEGRATED_EXECUTION_PLAN.md
│  └─ reference/
│     └─ fritzing/                   # Fritzing library files
├─ admin/                   # Administrative scripts
└─ fritzing/                # Legacy circuit diagrams
```

### Current Sensor Node Hardware

**Board #4: Heltec WiFi LoRa 32 V2** (integrated SX1276 LoRa + OLED display)

**Documentation:**
- **Architecture:** [`docs/architecture/board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md`](docs/architecture/board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md)
- **Wiring Guide:** [`docs/architecture/board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md`](docs/architecture/board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md)
- **System Architecture:** [`docs/architecture/ARCHITECTURE_PLAN_V2.md`](docs/architecture/ARCHITECTURE_PLAN_V2.md)
- **Legacy Designs:** [`docs/architecture/legacy/`](docs/architecture/legacy/)

**Sensors:**
1. RG-9 Rain Sensor (analog, GPIO36 with voltage divider)
2. RS485 Wind Sensor (pulse mode GPIO34 OR UART2 GPIO17/23)
3. MLX90614 IR Temperature (I²C 0x5A on GPIO21/22)
4. TSL2591 Sky Quality Meter (I²C 0x29 on GPIO21/22)

**Note:** Sensors use dedicated I²C bus (GPIO21/22), separate from OLED display bus (GPIO4/15).

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
   cd safety-monitor
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

**Note:** Application files are now in `safety-monitor/` subdirectory. Update service file paths accordingly.

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
WorkingDirectory=/home/user/skymonitor/safety-monitor
ExecStart=/home/user/skymonitor/venv/bin/python /home/user/skymonitor/safety-monitor/app.py
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
WorkingDirectory=/home/user/skymonitor/safety-monitor
ExecStart=/home/user/skymonitor/venv/bin/python /home/user/skymonitor/safety-monitor/control.py
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
- Use `python3 safety-monitor/test/serial_test_data.py` to generate serial data and follow port setting instructions.

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

   **Note:** If running files from `safety-monitor/`, adjust path to `~/github/skymonitor/safety-monitor/`
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
WorkingDirectory=/home/user/skymonitor/safety-monitor
ExecStart=/home/user/skymonitor/venv/bin/python /home/user/skymonitor/safety-monitor/system_monitor.py
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
   cd safety-monitor
   python app.py
   ```

2. Access the API endpoints:
   - Fetch latest sky data: `http://<your_server_ip>:<port>/api/sky_data`
   - Fetch latest metrics data: `http://<your_server_ip>:<port>/api/metrics_data`

These endpoints return the latest data from the respective tables in JSON format.