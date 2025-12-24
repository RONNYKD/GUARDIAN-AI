"""
Enable required Google Cloud APIs using gcloud CLI
"""

import subprocess
import sys
import time

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
        subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def enable_api(api_name, project_id):
    """Enable a single API"""
    try:
        result = subprocess.run(
            [
                "gcloud", "services", "enable",
                api_name,
                "--project", project_id
            ],
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def enable_all_apis(apis, project_id):
    """Enable all APIs at once (faster)"""
    api_list = list(apis.keys())
    try:
        print("🚀 Enabling all APIs in batch (faster)...")
        result = subprocess.run(
            ["gcloud", "services", "enable"] + api_list + ["--project", project_id],
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def main():
    """Main function to enable APIs"""
    print("🔧 GuardianAI - API Enablement")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}\n")
    
    # Check if gcloud is installed
    if not check_gcloud_installed():
        print("❌ gcloud CLI is not installed or not in PATH")
        print("\nPlease install gcloud CLI:")
        print("https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    print("✅ gcloud CLI detected\n")
    
    # Show APIs to enable
    print("📋 APIs to enable:")
    for api_name, description in REQUIRED_APIS.items():
        print(f"   • {api_name}")
        print(f"     {description}")
    
    print(f"\n   Total: {len(REQUIRED_APIS)} APIs")
    
    # Confirm
    response = input("\n❓ Proceed with enabling these APIs? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cancelled by user")
        sys.exit(0)
    
    print("\n" + "=" * 70)
    
    # Try batch enable first (faster)
    print("\n⏳ Enabling APIs (this may take 1-2 minutes)...\n")
    success, output = enable_all_apis(REQUIRED_APIS, PROJECT_ID)
    
    if success:
        print("✅ All APIs successfully enabled!\n")
        print(output)
        print("=" * 70)
        print("✅ Setup complete! You can now run:")
        print("   python check_apis.py")
        sys.exit(0)
    else:
        print("⚠️  Batch enable failed, trying individual enables...\n")
        
        # Enable individually
        success_count = 0
        failed_apis = []
        
        for api_name, description in REQUIRED_APIS.items():
            print(f"📦 Enabling {api_name}...")
            success, output = enable_api(api_name, PROJECT_ID)
            
            if success:
                print(f"   ✅ Enabled")
                success_count += 1
            else:
                print(f"   ❌ Failed: {output[:100]}")
                failed_apis.append((api_name, output))
            
            time.sleep(0.5)  # Small delay between requests
        
        print("\n" + "=" * 70)
        print(f"\n📊 Results: {success_count}/{len(REQUIRED_APIS)} APIs enabled")
        
        if failed_apis:
            print("\n❌ Failed APIs:")
            for api_name, error in failed_apis:
                print(f"   • {api_name}")
                print(f"     Error: {error[:150]}")
            
            print("\n💡 To enable manually:")
            print(f"   https://console.cloud.google.com/apis/library?project={PROJECT_ID}")
            sys.exit(1)
        else:
            print("\n✅ All APIs successfully enabled!")
            sys.exit(0)


if __name__ == "__main__":
    main()
