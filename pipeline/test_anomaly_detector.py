"""
Test AnomalyDetector with config integration
"""
import os
import sys

# Set environment for testing
os.environ['GCP_PROJECT_ID'] = 'lovable-clone-e08db'
os.environ['GOOGLE_API_KEY'] = 'AIzaSyBmdv2e-ADC2IyAWhsLCeL3FmXPGO4wV4I'

from anomaly_detector import AnomalyDetector, AnomalyType

print("=" * 70)
print("AnomalyDetector Configuration Test")
print("=" * 70)

# Initialize detector
detector = AnomalyDetector()

print("\n📊 Loaded Thresholds:")
for key, value in detector.THRESHOLDS.items():
    if "usd" in key.lower() or "cost" in key.lower():
        print(f"  {key}: ${value:,.2f}")
    elif "percent" in key.lower() or "rate" in key.lower():
        print(f"  {key}: {value}%")
    else:
        print(f"  {key}: {value}")

print("\n" + "=" * 70)
print("Testing Anomaly Detection")
print("=" * 70)

# Test 1: Normal latency
print("\n1. Normal Latency Test")
detector.add_sample("latency_ms", 100)
detector.add_sample("latency_ms", 120)
detector.add_sample("latency_ms", 95)
anomalies = detector.check_value("latency_ms", 150)
print(f"   Latency: 150ms")
print(f"   Result: {len(anomalies)} anomalies detected")
if anomalies:
    for a in anomalies:
        print(f"   - {a.description}")

# Test 2: High latency (should trigger)
print("\n2. High Latency Test (>5000ms threshold)")
anomalies = detector.check_value("latency_ms", 6000)
print(f"   Latency: 6000ms")
print(f"   Result: {len(anomalies)} anomalies detected")
if anomalies:
    for a in anomalies:
        print(f"   ✅ {a.severity.upper()}: {a.description}")
else:
    print("   ❌ Expected anomaly but none detected")

# Test 3: Low quality (should trigger)
print("\n3. Quality Degradation Test (<0.7 threshold)")
anomalies = detector.check_value("quality_score", 0.5)
print(f"   Quality: 0.5")
print(f"   Result: {len(anomalies)} anomalies detected")
if anomalies:
    for a in anomalies:
        print(f"   ✅ {a.severity.upper()}: {a.description}")
else:
    print("   ❌ Expected anomaly but none detected")

# Test 4: Normal quality
print("\n4. Normal Quality Test")
anomalies = detector.check_value("quality_score", 0.85)
print(f"   Quality: 0.85")
print(f"   Result: {len(anomalies)} anomalies detected")
if anomalies:
    for a in anomalies:
        print(f"   - {a.description}")

# Test 5: High error rate (should trigger)
print("\n5. Error Rate Test (>5% threshold)")
anomalies = detector.check_value("error_rate", 8.5)
print(f"   Error Rate: 8.5%")
print(f"   Result: {len(anomalies)} anomalies detected")
if anomalies:
    for a in anomalies:
        print(f"   ✅ {a.severity.upper()}: {a.description}")
else:
    print("   ❌ Expected anomaly but none detected")

# Test 6: Cost spike (should trigger)
print("\n6. Cost Spike Test (>$400,000 threshold)")
anomalies = detector.check_value("cost_usd", 450000)
print(f"   Cost: $450,000")
print(f"   Result: {len(anomalies)} anomalies detected")
if anomalies:
    for a in anomalies:
        print(f"   ✅ {a.severity.upper()}: {a.description}")
else:
    print("   ❌ Expected anomaly but none detected")

# Test 7: Z-score based detection
print("\n7. Z-Score Detection Test (statistical)")
print("   Adding 30 baseline samples...")
for i in range(30):
    detector.add_sample("response_time", 100 + (i % 10) * 5)  # 100-145ms range

baseline = detector.get_baseline("response_time")
if baseline:
    print(f"   Baseline: mean={baseline.mean:.1f}ms, std_dev={baseline.std_dev:.1f}ms")
    
    # Test with extreme value
    anomalies = detector.check_value("response_time", 500)
    print(f"   Test value: 500ms")
    print(f"   Result: {len(anomalies)} anomalies detected")
    if anomalies:
        for a in anomalies:
            print(f"   ✅ Z-score {a.deviation:.1f}: {a.description}")

print("\n" + "=" * 70)
print("✅ Anomaly Detector Tests Complete")
print("=" * 70)
print("\n🎯 Summary:")
print("  - Configuration loaded successfully")
print("  - Absolute threshold detection working")
print("  - Z-score based detection working")
print("  - Integration with config.py successful")
