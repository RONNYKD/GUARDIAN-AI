"""
Test Google AI Studio API availability
"""
import requests
import json

API_KEY = "AIzaSyBmdv2e-ADC2IyAWhsLCeL3FmXPGO4wV4I"

print("🔍 Testing Google AI Studio API access...")
print("=" * 60)

# Test simple generation
url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"

data = {
    "contents": [{
        "parts": [{"text": "Say hello in one word"}]
    }]
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text']
        print(f"✅ API Working!")
        print(f"Response: {text}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")
