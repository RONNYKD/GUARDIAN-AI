"""
Quick test script to create Datadog monitors with credentials from .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set credentials
os.environ['DD_API_KEY'] = '45c934d165bf8d9c475f9503e64c3f3b'
os.environ['DD_APP_KEY'] = 'cd27f925abb1d6b3e2b31ee444e4a228712d3e14'
os.environ['DD_SITE'] = 'datadoghq.com'

print("Loading Datadog Monitor Setup...")
from datadog_monitors import DatadogMonitorSetup

print("\nInitializing...")
setup = DatadogMonitorSetup()

print(f"\n✅ Configuration Loaded:")
print(f"  Environment: {setup.config.environment.value}")
print(f"  Cost Threshold: ${setup.config.thresholds.cost_anomaly_threshold_usd:,.0f}/day")
print(f"  Quality Threshold: {setup.config.thresholds.quality_degradation_threshold}")
print(f"  Latency Threshold: {setup.config.thresholds.latency_spike_threshold_ms}ms")
print(f"  Datadog Site: {setup.config.datadog.site}")

print("\n" + "=" * 60)
print("Options:")
print("  1. Create all monitors")
print("  2. List existing monitors")
print("  3. Delete all monitors")
print("  4. Show summary")
print("  5. Exit")
print("=" * 60)

choice = input("\nChoice (1-5): ").strip()

if choice == "1":
    print("\n🚀 Creating monitors...")
    monitors = setup.setup_all_monitors()
    print("\n✅ Monitor Creation Results:")
    for name, mid in monitors.items():
        if mid:
            print(f"  ✅ {name}: ID {mid}")
        else:
            print(f"  ❌ {name}: Failed")
    
    print(f"\n📊 Success: {sum(1 for m in monitors.values() if m)}/5 monitors created")
    print("\n🔗 View in Datadog: https://app.datadoghq.com/monitors/manage?q=tag:guardianai")

elif choice == "2":
    print("\n📋 Existing Monitors:")
    monitors = setup.list_guardianai_monitors()
    if monitors:
        for m in monitors:
            print(f"  - {m['name']} (ID: {m['id']})")
    else:
        print("  No GuardianAI monitors found")

elif choice == "3":
    confirm = input("\n⚠️  Delete all GuardianAI monitors? (yes/no): ").strip().lower()
    if confirm == "yes":
        deleted = setup.cleanup_all_monitors()
        print(f"\n✅ Deleted {deleted} monitors")
    else:
        print("\nCancelled")

elif choice == "4":
    import json
    summary = setup.get_monitor_summary()
    print("\n📊 Monitor Summary:")
    print(json.dumps(summary, indent=2))

else:
    print("\nExiting...")
