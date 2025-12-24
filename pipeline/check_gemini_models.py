"""
Test script to check which Gemini models are available in your project.
"""

import os
import sys

# Set credentials
os.environ["GCP_PROJECT_ID"] = "lovable-clone-e08db"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"d:\SENTINEL (for the google accelerator hackerthon)\lovable-clone-e08db-56b9ffba4711.json"

import vertexai
from vertexai.generative_models import GenerativeModel

project_id = "lovable-clone-e08db"

# Models to try
models_to_try = [
    "gemini-1.5-flash-002",
    "gemini-1.5-flash",
    "gemini-1.5-pro-002", 
    "gemini-1.5-pro",
    "gemini-1.0-pro-002",
    "gemini-1.0-pro",
    "gemini-pro",
]

# Regions to try
regions_to_try = [
    "us-central1",
    "us-east4",
    "us-west1",
    "us-west4",
    "europe-west1",
    "asia-southeast1",
]

print("🔍 Testing Gemini model availability...\n")
print("=" * 60)

found_working = False

for region in regions_to_try:
    print(f"\n📍 Region: {region}")
    print("-" * 60)
    
    for model_name in models_to_try:
        try:
            vertexai.init(project=project_id, location=region)
            model = GenerativeModel(model_name)
            
            # Try a simple generation
            response = model.generate_content("Say hello")
            
            print(f"✅ {model_name}: WORKS")
            print(f"   Response: {response.text[:50]}...")
            found_working = True
            
            if found_working:
                print(f"\n{'=' * 60}")
                print(f"🎉 SUCCESS! Use this configuration:")
                print(f"   Model: {model_name}")
                print(f"   Region: {region}")
                print(f"{'=' * 60}")
                sys.exit(0)
                
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                print(f"❌ {model_name}: Not found")
            elif "403" in error_msg:
                print(f"⚠️  {model_name}: Access denied (API not enabled)")
            else:
                print(f"⚠️  {model_name}: {error_msg[:80]}")

if not found_working:
    print(f"\n{'=' * 60}")
    print("❌ No working Gemini models found!")
    print("\nYou need to:")
    print("1. Enable Vertex AI API: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=lovable-clone-e08db")
    print("2. Enable Generative AI: https://console.cloud.google.com/vertex-ai/generative?project=lovable-clone-e08db")
    print("3. Accept terms of service for Gemini")
    print(f"{'=' * 60}")
    sys.exit(1)
