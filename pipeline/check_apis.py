"""
Check if required Google Cloud APIs are enabled for the project
Uses gcloud CLI to verify API status
"""

import subprocess
import json
import sys

# Project configuration
PROJECT_ID = "lovable-clone-e08db"

# Required APIs for GuardianAI
REQUIRED_APIS = {
    "aiplatform.googleapis.com": "Vertex AI (for Gemini models)",
    "generativelanguage.googleapis.com": "Generative Language API (Gemini)",
    "cloudfunctions.googleapis.com": "Cloud Functions",
    "firestore.googleapis.com": "Firestore",
    "cloudbuild.googleapis.com": "Cloud Build",
    "cloudresourcemanager.googleapis.com": "Cloud Resource Manager",
    "serviceusage.googleapis.com": "Service Usage API",
    "logging.googleapis.com": "Cloud Logging",
    "pubsub.googleapis.com": "Cloud Pub/Sub",
    "run.googleapis.com": "Cloud Run",
    "artifactregistry.googleapis.com": "Artifact Registry",
}


def check_gcloud_installed():
    """Check if gcloud CLI is installed"""
    try:
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            check=True,
            shell=True  # Use shell on Windows to find gcloud in PATH
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_enabled_apis(project_id):
    """Get list of enabled APIs for the project"""
    try:
        result = subprocess.run(
            [
                "gcloud", "services", "list",
                "--enabled",
                "--project", project_id,
                "--format", "json"
            ],
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting enabled APIs: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing API list: {e}")
        return []


def check_api_status(api_name, enabled_apis):
    """Check if a specific API is enabled"""
    enabled_api_names = [api.get("config", {}).get("name", "") for api in enabled_apis]
    return api_name in enabled_api_names


def main():
    """Main function to check API status"""
    print("🔍 GuardianAI - API Status Check")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}\n")
    
    # Check if gcloud is installed
    if not check_gcloud_installed():
        print("❌ gcloud CLI is not installed or not in PATH")
        print("\nPlease install gcloud CLI:")
        print("https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    print("✅ gcloud CLI detected\n")
    
    # Get enabled APIs
    print("📡 Fetching enabled APIs...")
    enabled_apis = get_enabled_apis(PROJECT_ID)
    
    if not enabled_apis:
        print("⚠️  Could not retrieve API list. Check your authentication and permissions.")
        sys.exit(1)
    
    print(f"Found {len(enabled_apis)} enabled APIs\n")
    
    # Check each required API
    print("📋 Required APIs Status:")
    print("-" * 70)
    
    all_enabled = True
    disabled_apis = []
    
    for api_name, description in REQUIRED_APIS.items():
        is_enabled = check_api_status(api_name, enabled_apis)
        status = "✅ ENABLED " if is_enabled else "❌ DISABLED"
        print(f"{status} | {api_name}")
        print(f"          {description}")
        
        if not is_enabled:
            all_enabled = False
            disabled_apis.append(api_name)
    
    print("-" * 70)
    
    # Summary
    print("\n📊 Summary:")
    enabled_count = len(REQUIRED_APIS) - len(disabled_apis)
    print(f"   Enabled:  {enabled_count}/{len(REQUIRED_APIS)}")
    print(f"   Disabled: {len(disabled_apis)}/{len(REQUIRED_APIS)}")
    
    # Action items
    if not all_enabled:
        print("\n⚠️  ACTION REQUIRED: Some APIs are not enabled")
        print("\n💡 To enable disabled APIs, run:")
        print(f"\n   python enable_apis_gcloud.py")
        print("\n   Or manually enable them:")
        for api in disabled_apis:
            print(f"   gcloud services enable {api} --project={PROJECT_ID}")
        
        print(f"\n   Or via console:")
        print(f"   https://console.cloud.google.com/apis/library?project={PROJECT_ID}")
        sys.exit(1)
    else:
        print("\n✅ All required APIs are enabled!")
        print("   Your project is ready to use GuardianAI.")
        sys.exit(0)


if __name__ == "__main__":
    main()
