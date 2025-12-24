"""
Enable required Google Cloud APIs using Python (no gcloud CLI needed)
"""

import os
from google.cloud import service_usage_v1
from google.oauth2 import service_account

# Set credentials
credentials_path = r"d:\SENTINEL (for the google accelerator hackerthon)\lovable-clone-e08db-56b9ffba4711.json"
project_id = "lovable-clone-e08db"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

print("🔧 Enabling Google Cloud APIs...\n")
print("=" * 60)

# APIs to enable
apis_to_enable = [
    "aiplatform.googleapis.com",           # Vertex AI
    "generativelanguage.googleapis.com",   # Gemini API
    "cloudresourcemanager.googleapis.com", # Resource Manager
    "serviceusage.googleapis.com",         # Service Usage API
]

try:
    # Create credentials
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path
    )
    
    # Create client
    client = service_usage_v1.ServiceUsageClient(credentials=credentials)
    
    for api in apis_to_enable:
        print(f"\n📦 Enabling {api}...")
        
        try:
            # Enable the service
            service_name = f"projects/{project_id}/services/{api}"
            
            # Check if already enabled
            request = service_usage_v1.GetServiceRequest(name=service_name)
            service = client.get_service(request=request)
            
            if service.state == service_usage_v1.State.ENABLED:
                print(f"   ✅ Already enabled")
            else:
                # Enable the service
                enable_request = service_usage_v1.EnableServiceRequest(name=service_name)
                operation = client.enable_service(request=enable_request)
                
                print(f"   ⏳ Enabling... (this may take 1-2 minutes)")
                operation.result()  # Wait for completion
                print(f"   ✅ Successfully enabled")
                
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "PERMISSION_DENIED" in error_msg:
                print(f"   ❌ Permission denied - service account needs serviceusage.services.enable permission")
                print(f"      You'll need to enable this manually in the console")
            elif "404" in error_msg:
                print(f"   ⚠️  API not found or not available in this project")
            else:
                print(f"   ❌ Error: {error_msg[:100]}")
    
    print("\n" + "=" * 60)
    print("✅ API enablement process complete!")
    print("\nNote: If you got permission errors, you need to:")
    print("1. Go to: https://console.cloud.google.com/iam-admin/iam?project=lovable-clone-e08db")
    print("2. Find: guraina-ai@lovable-clone-e08db.iam.gserviceaccount.com")
    print("3. Add role: Service Usage Admin")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Failed to initialize: {e}")
    print("\nYou need to enable APIs manually in the console:")
    print("👉 https://console.cloud.google.com/apis/library?project=lovable-clone-e08db")
