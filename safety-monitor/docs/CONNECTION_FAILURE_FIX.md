# Connection Failure Fix Summary

**Date:** 2025-12-21  
**Issue:** Systematic connection failures between app.py (port 5000) and control.py (port 5001)

---

## 🔍 Root Causes Identified

### **Critical Issue #1: Legacy Serial Fields in Settings UI**
**Severity:** CRITICAL - Causes 500 Internal Server Error

**Problem:**
- [`settings.html`](templates/settings.html) referenced non-existent settings keys:
  - `temp_hum_url`
  - `serial_port_rain`
  - `serial_port_json`
  - `baud_rate`
- These keys do NOT exist in [`settings.json`](settings.json)
- Jinja template engine threw `KeyError` → HTTP 500 error on `/settings` page

**Root Cause:** Serial support was removed in architecture V2, but UI templates were not updated

---

### **Critical Issue #2: Silent Flask API Startup Failures**
**Severity:** HIGH - Explains port 5001 unreachability

**Problem:**
- [`control.py`](control.py:498-506) starts Flask in daemon thread
- Logs "Local API started" BEFORE Flask actually binds to port
- If `app.run()` fails (port busy, permission denied, import error), exception only visible in thread
- No verification that API is actually reachable

**Root Cause:** Daemon thread error handling + premature success logging

---

### **Issue #3: UI Routes Crash When Control Service Unavailable**
**Severity:** MEDIUM - Poor user experience

**Problem:**
- [`/dashboard`](app.py:169-174) route had no error handling
- If control service down → crashes with 500 error
- Should show "control service unreachable" message instead

---

## ✅ Fixes Applied

### **Fix #1: Remove Legacy Serial Fields from Settings UI**
**File:** [`safety-monitor/templates/settings.html`](templates/settings.html)

**Changes:**
- ❌ Removed: `temp_hum_url`, `serial_port_rain`, `serial_port_json`, `baud_rate` fields
- ✅ Added: Current architecture fields:
  - `control_port` (control service port)
  - `primary_endpoint` (primary sensor HTTP endpoint)
  - `fallback_endpoint` (fallback sensor HTTP endpoint)
  - `primary_failure_threshold` (failures before fallback)
  - `max_data_age_seconds` (stale data threshold)
  - `http_timeout_seconds` (HTTP request timeout)
  - `heater_min_off_time_seconds` (heater safety interval)

**Result:** Settings page now reflects current HTTP/LoRa architecture only

---

### **Fix #2: Add Flask Startup Verification to control.py**
**File:** [`safety-monitor/control.py`](control.py:495-540)

**Changes:**
1. Wrapped `app.run()` in explicit error handler that logs exceptions
2. Added 1-second delay after thread start to allow Flask to bind
3. Added socket connection test to verify port 5001 is actually reachable
4. Clear logging:
   - ✓ "Flask API successfully bound to http://127.0.0.1:5001"
   - ✗ "Flask API NOT reachable on port 5001"
   - ✗ "FATAL: Flask API failed to start: {error}"

**Result:** Control service now confirms API is reachable before claiming success

---

### **Fix #3: Add Graceful Error Handling to app.py Routes**
**File:** [`safety-monitor/app.py`](app.py:169-200)

**Changes:**
- Added try/except wrapper to `/dashboard` route
- Provides safe defaults when control service unavailable:
  ```python
  status = {"error": "Control service unreachable", ...}
  health = {"error": "Control service unreachable", ...}
  ```
- Never returns 500 error to user when control service is down

**Result:** UI stays functional even when control service is unavailable

---

### **Fix #4: Update Dashboard Template Error Display**
**File:** [`safety-monitor/templates/dashboard.html`](templates/dashboard.html)

**Changes:**
1. Added error banner when control service unavailable:
   - Shows clear "Control Service Unavailable" message
   - Displays troubleshooting steps (systemctl status, journalctl, lsof)
2. Conditionally renders metrics chart only when control service is reachable
3. JavaScript error handling for failed `/api/metrics_data` fetch

**Result:** Dashboard shows helpful diagnostic info instead of crashing

---

## 🎯 Expected Outcomes

After these fixes:

1. **Settings page loads correctly** - No more KeyError / 500 errors
2. **control.py logs startup success/failure clearly** - Easy to diagnose port binding issues
3. **UI routes never crash** - Show "control service unreachable" instead of 500 errors
4. **Dashboard provides troubleshooting guidance** - Users know how to fix control service issues

---

## 📋 Testing Checklist

### Test Scenario 1: Normal Operation
- [ ] Start control.py: `python3 control.py`
- [ ] Verify log shows: "✓ Flask API successfully bound to http://127.0.0.1:5001"
- [ ] Start app.py: `python3 app.py`
- [ ] Access http://allsky.local:5000 - should load normally
- [ ] Access http://allsky.local:5000/settings - should show current settings (no serial fields)
- [ ] Access http://allsky.local:5000/dashboard - should show metrics
- [ ] Access http://allsky.local:5001/health - should return JSON
- [ ] Test manual controls (fan on/off, heater on/off) - should work

### Test Scenario 2: Control Service Down
- [ ] Stop control.py
- [ ] Access http://allsky.local:5000 - should show "last_error: Control service unreachable"
- [ ] Access http://allsky.local:5000/dashboard - should show error banner with troubleshooting
- [ ] Access http://allsky.local:5000/settings - should still work (reads settings.json directly)
- [ ] Try manual controls - should show error flash message

### Test Scenario 3: Port Conflict
- [ ] Start dummy service on port 5001: `nc -l 5001`
- [ ] Start control.py: `python3 control.py`
- [ ] Verify log shows: "✗ Flask API NOT reachable on port 5001"
- [ ] OR: "FATAL: Flask API failed to start: [Errno 98] Address already in use"

---

## 🔧 Systemd Service Deployment

If using systemd services, restart them to apply changes:

```bash
# Restart control service
sudo systemctl restart control.service

# Check status and logs
sudo systemctl status control.service
sudo journalctl -u control.service -n 50 --no-pager

# Look for startup confirmation:
# "✓ Flask API successfully bound to http://127.0.0.1:5001"

# Restart web UI service (if applicable)
sudo systemctl restart app.service
```

---

## 📝 Architecture Notes

### Current Architecture (V2)
- **HTTP polling** via MeetJeStad API endpoints
- **LoRa fallback** for embedded sensors (future)
- **NO serial communication** - fully removed

### Port Configuration
- **Port 5000:** Flask web UI (app.py) - public-facing
- **Port 5001:** Control service API (control.py) - localhost only
- Both read from [`settings.json`](settings.json) → `control_port` key

### Inter-Service Communication
```
User Browser → http://allsky.local:5000 (app.py)
                     ↓
              http://127.0.0.1:5001 (control.py)
                     ↓
              HTTP sensor endpoints (MeetJeStad)
```

---

## 🚨 Known Limitations

1. **1-second delay on control.py startup** - Needed for Flask socket test
   - Acceptable for service startup
   - Alternative: Use `werkzeug` lifecycle hooks (more complex)

2. **Daemon thread for Flask** - Still used for background API
   - Simpler than multiprocessing
   - Control loop runs in main thread (correct design)
   - Errors now logged explicitly

3. **Memory threshold not persisted** - UI shows field but POST handler ignores it
   - Non-critical: System monitoring not currently used
   - Can be added if needed: `settings['memory_usage_threshold'] = int(request.form.get(...))`

---

## 📚 Related Documentation

- [`SERIAL_REMOVAL_SUMMARY.md`](../SERIAL_REMOVAL_SUMMARY.md) - Architecture V2 changes
- [`ARCHITECTURE_PLAN_V2.md`](../docs/architecture/ARCHITECTURE_PLAN_V2.md) - Current system design
- [`admin/UPDATE_SERVICES.md`](../admin/UPDATE_SERVICES.md) - Service deployment guide
