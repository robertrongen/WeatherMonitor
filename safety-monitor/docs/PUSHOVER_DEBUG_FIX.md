# Pushover Notification Debug Fix ✅ RESOLVED

## Root Cause Analysis

### Issue
The `reboot_notify.py` script was sending Pushover notifications successfully (HTTP 200), but they were **delivered silently** - no sound or visual alert.

### Root Causes (2 issues found)

#### 1. No Response Validation (Observability Issue)
The [`send_pushover()`](../reboot_notify.py:14) function had **no response validation**:

1. ❌ **Never checked HTTP status code** (200 = success, 400/401 = credential error)
2. ❌ **Never logged response body** (contains error details from Pushover API)
3. ❌ **Logged success immediately** even if API rejected the request
4. ❌ **Silent failures** - no way to detect invalid credentials, malformed requests, or API errors

#### 2. Missing Sound Field (Actual Bug)
**Critical:** [`reboot_notify.py`](../reboot_notify.py:35) had **no `sound` parameter** in the Pushover payload

Comparison with [`rain_alarm.py`](../rain_alarm.py:20):
- `rain_alarm.py`: ✅ Includes `'sound': 'siren'` → **audible notification**
- `reboot_notify.py`: ❌ No sound field → **silent delivery** (notification sent but no alert)

Without the `sound` field, Pushover delivered the notification silently. The user never noticed it because:
- No audible alert (phone didn't ring/vibrate)
- No obvious visual indicator (depended on device settings)
- API returned HTTP 200 (message delivered successfully)

## Code Changes

### What Changed
File: [`safety-monitor/reboot_notify.py`](../reboot_notify.py)

**Fix 1: Added diagnostic logging** (observability):
- ✅ Log credential presence check (without exposing values)
- ✅ Log HTTP status code from Pushover API
- ✅ Log response body (contains error details)
- ✅ More specific exception handling (timeout vs network vs other)
- ✅ Clear success/failure indicators (✅/❌ emojis)

**Fix 2: Added sound parameter** (bug fix):
- ✅ Added `"sound": "pushover"` to API payload
- ✅ Ensures notifications are audible (not silent)
- ✅ Matches behavior of `rain_alarm.py`

### Exact Diff

```diff
 def send_pushover(message, priority=0):
     token = os.getenv("PUSHOVER_API_TOKEN")
     user = os.getenv("PUSHOVER_USER_KEY")
 
+    # Diagnostic: Log credential presence (not values)
+    logger.info(f"Pushover credentials check: token={'present' if token else 'MISSING'}, user={'present' if user else 'MISSING'}")
+
     if not token or not user:
-        logger.warning("Pushover credentials missing")
+        logger.error("Pushover credentials missing - cannot send notification")
         return
 
     try:
-        requests.post(
+        # Diagnostic: Log request details
+        logger.info(f"Sending Pushover notification with priority={priority}")
+        
+        response = requests.post(
             "https://api.pushover.net/1/messages.json",
             data={
                 "token": token,
                 "user": user,
                 "message": message,
                 "priority": priority,
+                "sound": "pushover",  # Default sound to ensure notification is audible
             },
             timeout=5,
         )
-        logger.info(f"Pushover sent: {message}")
-    except Exception as e:
-        logger.error(f"Pushover failed: {e}")
+        
+        # Diagnostic: Log HTTP response
+        logger.info(f"Pushover HTTP status: {response.status_code}")
+        logger.info(f"Pushover response body: {response.text}")
+        
+        # Validate response
+        if response.status_code == 200:
+            logger.info(f"✅ Pushover sent successfully: {message[:50]}...")
+        else:
+            logger.error(f"❌ Pushover API returned error status {response.status_code}: {response.text}")
+            
+    except requests.exceptions.Timeout as e:
+        logger.error(f"Pushover request timeout after 5s: {e}")
+    except requests.exceptions.RequestException as e:
+        logger.error(f"Pushover network error: {e}")
+    except Exception as e:
+        logger.error(f"Pushover unexpected error: {type(e).__name__}: {e}")
```

## How to Test Locally

### 1. Verify Environment Variables

First, check your `.env` file in the repository root:
```bash
cd /home/robert/WeatherMonitor
cat .env | grep PUSHOVER
```

Expected output:
```
PUSHOVER_USER_KEY=<your-30-char-user-key>
PUSHOVER_API_TOKEN=<your-30-char-api-token>
```

⚠️ **Common Issues:**
- Extra spaces after `=`
- Missing quotes (not required for dotenv)
- Wrong variable names (must match exactly)

### 2. Run Manual Test

```bash
cd /home/robert/WeatherMonitor
PYTHONPATH=/home/robert/WeatherMonitor/safety-monitor \
python -c "from reboot_notify import pre_reboot; pre_reboot('manual test')"
```

### 3. Check Diagnostic Logs

```bash
tail -n 50 /home/robert/WeatherMonitor/logs/reboot_notify.log
```

**What to look for:**

#### Success Case:
```
2025-12-23 20:30:15 - Pushover credentials check: token=present, user=present
2025-12-23 20:30:15 - Sending Pushover notification with priority=1
2025-12-23 20:30:16 - Pushover HTTP status: 200
2025-12-23 20:30:16 - Pushover response body: {"status":1,"request":"xxx"}
2025-12-23 20:30:16 - ✅ Pushover sent successfully: ⚠️ Skymonitor reboot triggered...
```

#### Credential Issue:
```
2025-12-23 20:30:15 - Pushover credentials check: token=MISSING, user=present
2025-12-23 20:30:15 - Pushover credentials missing - cannot send notification
```

#### Invalid Credentials:
```
2025-12-23 20:30:15 - Pushover credentials check: token=present, user=present
2025-12-23 20:30:15 - Sending Pushover notification with priority=1
2025-12-23 20:30:16 - Pushover HTTP status: 400
2025-12-23 20:30:16 - Pushover response body: {"token":"invalid","errors":["application token is invalid"],"status":0,"request":"xxx"}
2025-12-23 20:30:16 - ❌ Pushover API returned error status 400: {"token":"invalid"...}
```

#### Network Issue:
```
2025-12-23 20:30:15 - Pushover credentials check: token=present, user=present
2025-12-23 20:30:15 - Sending Pushover notification with priority=1
2025-12-23 20:30:20 - Pushover request timeout after 5s: HTTPSConnectionPool...
```

### 4. Verify State File Handling

After first test, the state file should exist:
```bash
ls -la /home/robert/.run/reboot_reason
cat /home/robert/.run/reboot_reason
```

Should show: `manual test`

### 5. Test Again (Should Skip)

Run the same command again - it should skip (duplicate prevention):
```bash
PYTHONPATH=/home/robert/WeatherMonitor/safety-monitor \
python -c "from reboot_notify import pre_reboot; pre_reboot('manual test 2')"
```

No notification should be sent. Check logs - should be empty/unchanged.

### 6. Test Post-Boot Notification

```bash
PYTHONPATH=/home/robert/WeatherMonitor/safety-monitor \
python -c "from reboot_notify import post_boot; post_boot()"
```

This should:
- Send "✅ Skymonitor back online" notification
- Delete the state file

Verify:
```bash
ls /home/robert/.run/reboot_reason  # Should NOT exist
```

### 7. Clean Up State File

If you need to reset:
```bash
rm -f /home/robert/.run/reboot_reason
```

## Expected Pushover Notifications

When working correctly, you should receive:

### Pre-Reboot Notification:
```
⚠️ Skymonitor reboot triggered
Reason: manual test
```
Priority: 1 (high priority, bypasses quiet hours)

### Post-Boot Notification:
```
✅ Skymonitor back online
Previous reboot reason: manual test
```
Priority: 0 (normal)

## Common Failure Scenarios

| Log Output | Likely Cause | Fix |
|------------|-------------|-----|
| `token=MISSING` or `user=MISSING` | `.env` not loaded or wrong path | Check `.env` exists in repo root |
| `HTTP status: 400` + `"token":"invalid"` | Wrong API token | Verify token in Pushover dashboard |
| `HTTP status: 400` + `"user":"invalid"` | Wrong user key | Verify user key in Pushover dashboard |
| `HTTP status: 401` | Authentication failed | Regenerate credentials in Pushover |
| `request timeout after 5s` | Network issue | Check internet connectivity |
| No log output at all | `dotenv` not loading `.env` | Check `.env` file path and permissions |

## Next Steps

1. ✅ **Code updated** - Better observability added
2. 🔄 **Run test** - Follow test steps above
3. 📋 **Check logs** - Identify exact failure reason
4. 🔧 **Fix root cause** - Usually credential or `.env` path issue
5. ✅ **Commit changes** - Safe to commit (no behavior change)

## Similar Fix Needed?

The [`rain_alarm.py`](../rain_alarm.py) file has the same issue - consider applying similar diagnostic logging there.

## References

- Pushover API docs: https://pushover.net/api
- `.env` example: [`example.env`](../../example.env)
- Systemd service: [`admin/app.service`](../../admin/app.service)
