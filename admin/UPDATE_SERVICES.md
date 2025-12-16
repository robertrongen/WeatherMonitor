# Systemd Service Path Updates (Post-Reorganization)

**Required Action:** Update systemd service files to reflect new `safety-monitor/` path.

## Updated Service Files

### app.service
```bash
sudo nano /etc/systemd/system/app.service
```

Content (updated paths in **bold**):
```ini
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

###control.service
```bash
sudo nano /etc/systemd/system/control.service
```

Content (updated paths in **bold**):
```ini
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

### system_monitor.service
```bash
sudo nano /etc/systemd/system/system_monitor.service
```

Content (updated paths in **bold**):
```ini
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

## Apply Changes

After editing service files:
```bash
sudo systemctl daemon-reload
sudo systemctl restart app control system_monitor
sudo systemctl status app control system_monitor
```

## Validation

Check that services start without errors:
```bash
sudo journalctl -u app.service -n 50
sudo journalctl -u control.service -n 50
sudo journalctl -u system_monitor.service -n 50
```

Verify web UI accessible: `http://allsky.local:5000`
