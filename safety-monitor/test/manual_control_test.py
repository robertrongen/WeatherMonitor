#!/usr/bin/env python3
"""Test manual actuator control endpoints"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json

CONTROL_API_URL = "http://127.0.0.1:5001"
FLASK_UI_URL = "http://127.0.0.1:5000"

def test_control_status():
    """Test /status endpoint returns mode information"""
    print("Testing /status endpoint...")
    try:
        response = requests.get(f"{CONTROL_API_URL}/status", timeout=2)
        response.raise_for_status()
        status = response.json()
        
        print(f"  Mode: {status.get('mode')}")
        print(f"  Fan: {status.get('fan_status')} ({status.get('fan_mode')})")
        print(f"  Heater: {status.get('heater_status')} ({status.get('heater_mode')})")
        
        assert 'fan_mode' in status, "fan_mode missing from status"
        assert 'heater_mode' in status, "heater_mode missing from status"
        assert status['fan_mode'] in ['AUTO', 'MANUAL'], f"Invalid fan_mode: {status['fan_mode']}"
        assert status['heater_mode'] in ['AUTO', 'MANUAL'], f"Invalid heater_mode: {status['heater_mode']}"
        
        print("  ✓ Status endpoint test passed\n")
        return True
    except Exception as e:
        print(f"  ✗ Status endpoint test failed: {e}\n")
        return False

def test_fan_control():
    """Test fan manual control via /actuators endpoint"""
    print("Testing fan control...")
    
    # Test fan ON
    print("  Setting fan to ON...")
    try:
        response = requests.post(f"{CONTROL_API_URL}/actuators", 
                                json={"fan": "on"}, timeout=2)
        response.raise_for_status()
        result = response.json()
        print(f"    Response: {json.dumps(result, indent=2)}")
        assert result.get('applied_state', {}).get('fan_mode') == 'MANUAL'
        print("    ✓ Fan set to MANUAL ON\n")
    except Exception as e:
        print(f"    ✗ Failed: {e}\n")
        return False
    
    # Test fan AUTO
    print("  Setting fan to AUTO...")
    try:
        response = requests.post(f"{CONTROL_API_URL}/actuators", 
                                json={"fan": "auto"}, timeout=2)
        response.raise_for_status()
        result = response.json()
        print(f"    Response: {json.dumps(result, indent=2)}")
        assert result.get('applied_state', {}).get('fan_mode') == 'AUTO'
        print("    ✓ Fan set to AUTO\n")
    except Exception as e:
        print(f"    ✗ Failed: {e}\n")
        return False
    
    return True

def test_heater_control():
    """Test heater manual control via /actuators endpoint"""
    print("Testing heater control...")
    
    # Test heater ON (may be rejected by safety validation)
    print("  Setting heater to ON...")
    try:
        response = requests.post(f"{CONTROL_API_URL}/actuators", 
                                json={"heater": "on"}, timeout=2)
        response.raise_for_status()
        result = response.json()
        print(f"    Response: {json.dumps(result, indent=2)}")
        assert result.get('applied_state', {}).get('heater_mode') == 'MANUAL'
        print("    ✓ Heater set to MANUAL (safety validation applied)\n")
    except Exception as e:
        print(f"    ✗ Failed: {e}\n")
        return False
    
    # Test heater AUTO
    print("  Setting heater to AUTO...")
    try:
        response = requests.post(f"{CONTROL_API_URL}/actuators", 
                                json={"heater": "auto"}, timeout=2)
        response.raise_for_status()
        result = response.json()
        print(f"    Response: {json.dumps(result, indent=2)}")
        assert result.get('applied_state', {}).get('heater_mode') == 'AUTO'
        print("    ✓ Heater set to AUTO\n")
    except Exception as e:
        print(f"    ✗ Failed: {e}\n")
        return False
    
    return True

def test_reset_control():
    """Test reset to AUTO for both actuators"""
    print("Testing reset to AUTO...")
    try:
        response = requests.post(f"{CONTROL_API_URL}/actuators", 
                                json={"fan": "auto", "heater": "auto"}, timeout=2)
        response.raise_for_status()
        result = response.json()
        print(f"  Response: {json.dumps(result, indent=2)}")
        
        assert result.get('applied_state', {}).get('fan_mode') == 'AUTO'
        assert result.get('applied_state', {}).get('heater_mode') == 'AUTO'
        print("  ✓ Both actuators reset to AUTO\n")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
        return False

def test_invalid_command():
    """Test invalid command handling"""
    print("Testing invalid command...")
    try:
        response = requests.post(f"{CONTROL_API_URL}/actuators", 
                                json={"fan": "invalid"}, timeout=2)
        response.raise_for_status()
        result = response.json()
        print(f"  Response: {json.dumps(result, indent=2)}")
        
        # Should have an error in the fan response
        assert 'error' in result.get('fan', {})
        print("  ✓ Invalid command properly rejected\n")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("MANUAL ACTUATOR CONTROL TEST SUITE")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("  - control.py service running on port 5001")
    print("  - Valid sensor data available")
    print()
    
    tests = [
        ("Status Endpoint", test_control_status),
        ("Fan Control", test_fan_control),
        ("Heater Control", test_heater_control),
        ("Reset Control", test_reset_control),
        ("Invalid Command", test_invalid_command)
    ]
    
    results = []
    for test_name, test_func in tests:
        print("-" * 60)
        result = test_func()
        results.append((test_name, result))
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)
