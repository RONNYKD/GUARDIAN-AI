"""
Test script for Demo Mode API endpoints

Tests all 5 endpoints:
1. POST /api/demo/launch-attack
2. POST /api/demo/run-scenario
3. GET /api/demo/status/{scenario_id}
4. GET /api/demo/stats
5. POST /api/demo/reset
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def test_launch_attack():
    """Test launching a single attack."""
    print("\n" + "="*70)
    print("TEST 1: Launch Attack (Prompt Injection)")
    print("="*70)
    
    payload = {
        "attack_type": "prompt_injection",
        "count": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/demo/launch-attack", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['message']}")
        print(f"   Records generated: {data['records_generated']}")
        print(f"   Trace IDs: {data['trace_ids'][:2]}...")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False


def test_run_scenario():
    """Test running a preset scenario."""
    print("\n" + "="*70)
    print("TEST 2: Run Scenario (Security Breach)")
    print("="*70)
    
    payload = {
        "scenario_type": "security_breach",
        "speed": "fast"
    }
    
    response = requests.post(f"{BASE_URL}/api/demo/run-scenario", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['message']}")
        print(f"   Scenario ID: {data['scenario_id']}")
        print(f"   Estimated duration: {data['estimated_duration_seconds']}s")
        return data['scenario_id']
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None


def test_scenario_status(scenario_id):
    """Test getting scenario status."""
    print("\n" + "="*70)
    print("TEST 3: Get Scenario Status")
    print("="*70)
    
    # Poll a few times
    for i in range(3):
        response = requests.get(f"{BASE_URL}/api/demo/status/{scenario_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Poll {i+1}: {data['status']} - {data['progress_percent']}% - Step: {data['current_step']}")
            print(f"   Steps: {data['steps_completed']}/{data['total_steps']}, Records: {data['records_generated']}")
            
            if data['status'] == 'completed':
                print(f"✅ Scenario completed!")
                return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
        
        time.sleep(2)
    
    print("✅ Status polling working")
    return True


def test_get_stats():
    """Test getting demo statistics."""
    print("\n" + "="*70)
    print("TEST 4: Get Demo Stats")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/demo/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Total requests: {data['total_requests']}")
        print(f"   Threats detected: {data['threat_count']}")
        print(f"   Threat breakdown: {data['threat_breakdown']}")
        print(f"   Avg quality: {data['avg_quality_score']}")
        print(f"   Total cost: ${data['total_cost_usd']}")
        print(f"   Avg latency: {data['avg_latency_ms']}ms")
        print(f"   Error rate: {data['error_rate_percent']}%")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False


def test_reset():
    """Test resetting demo data."""
    print("\n" + "="*70)
    print("TEST 5: Reset Demo Data")
    print("="*70)
    
    response = requests.post(f"{BASE_URL}/api/demo/reset")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['message']}")
        print(f"   Records deleted: {data['records_deleted']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("GuardianAI Demo Mode API Tests")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print("\nNOTE: Make sure the backend is running with:")
    print("  cd backend && uvicorn main:app --reload")
    
    input("\nPress Enter to start tests...")
    
    results = []
    
    # Test 1: Launch Attack
    results.append(("Launch Attack", test_launch_attack()))
    time.sleep(1)
    
    # Test 2: Run Scenario
    scenario_id = test_run_scenario()
    results.append(("Run Scenario", scenario_id is not None))
    time.sleep(1)
    
    # Test 3: Scenario Status
    if scenario_id:
        results.append(("Scenario Status", test_scenario_status(scenario_id)))
        time.sleep(1)
    
    # Test 4: Get Stats
    results.append(("Get Stats", test_get_stats()))
    time.sleep(1)
    
    # Test 5: Reset (optional - uncomment to test)
    # results.append(("Reset Data", test_reset()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
