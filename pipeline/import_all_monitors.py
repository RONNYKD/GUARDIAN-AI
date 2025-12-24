"""
Bulk import all GuardianAI monitors from JSON files
"""
import os
import json
from pathlib import Path
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.model.monitor import Monitor

# Set up credentials
os.environ['DD_API_KEY'] = '45c934d165bf8d9c475f9503e64c3f3b'
os.environ['DD_APP_KEY'] = 'cd27f925abb1d6b3e2b31ee444e4a228712d3e14'

# Configure Datadog API
configuration = Configuration()
configuration.api_key["apiKeyAuth"] = os.getenv("DD_API_KEY")
configuration.api_key["appKeyAuth"] = os.getenv("DD_APP_KEY")
configuration.server_variables["site"] = "datadoghq.com"

print("=" * 70)
print("GuardianAI - Bulk Monitor Import")
print("=" * 70)

# Get all JSON files
monitors_dir = Path(__file__).parent / "datadog_monitors"
json_files = sorted(monitors_dir.glob("*.json"))

if not json_files:
    print("\n❌ No JSON files found in datadog_monitors/")
    exit(1)

print(f"\nFound {len(json_files)} monitor files:")
for f in json_files:
    print(f"  - {f.name}")

print("\n" + "=" * 70)
print("Importing monitors...")
print("=" * 70)

results = []

with ApiClient(configuration) as api_client:
    api_instance = MonitorsApi(api_client)
    
    for json_file in json_files:
        try:
            # Load JSON
            with open(json_file, 'r') as f:
                monitor_data = json.load(f)
            
            monitor_name = monitor_data.get('name', json_file.name)
            print(f"\n📤 Importing: {monitor_name}")
            
            # Create monitor
            monitor = Monitor(**monitor_data)
            response = api_instance.create_monitor(body=monitor)
            
            print(f"   ✅ Created successfully! (ID: {response.id})")
            results.append({
                'file': json_file.name,
                'name': monitor_name,
                'id': response.id,
                'status': 'success'
            })
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}")
            results.append({
                'file': json_file.name,
                'name': monitor_name,
                'status': 'failed',
                'error': str(e)
            })

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)

success_count = sum(1 for r in results if r['status'] == 'success')
failed_count = len(results) - success_count

print(f"\n✅ Successfully imported: {success_count}/{len(results)}")
print(f"❌ Failed: {failed_count}/{len(results)}")

if success_count > 0:
    print("\n📋 Created Monitors:")
    for r in results:
        if r['status'] == 'success':
            print(f"  - {r['name']} (ID: {r['id']})")

if failed_count > 0:
    print("\n⚠️  Failed Monitors:")
    for r in results:
        if r['status'] == 'failed':
            print(f"  - {r['file']}: {r.get('error', 'Unknown error')[:80]}")

print("\n🔗 View in Datadog:")
print("   https://app.datadoghq.com/monitors/manage?q=tag:guardianai")
print("\n" + "=" * 70)
