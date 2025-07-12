#!/usr/bin/env python3
"""
Quick test script to verify the API is working
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Google Scholar Profile Analyzer API")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: API documentation
    print("\n2. Testing API docs endpoint...")
    try:
        response = requests.get(f"{base_url}/docs", allow_redirects=False)
        if response.status_code in [200, 307]:  # 307 is redirect to /docs
            print("✅ API docs accessible")
        else:
            print(f"⚠️  API docs status: {response.status_code}")
    except Exception as e:
        print(f"❌ API docs error: {e}")
    
    # Test 3: Root endpoint
    print("\n3. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    print(f"\n📋 Summary:")
    print(f"   Backend URL: {base_url}")
    print(f"   Frontend URL: http://localhost:3002")
    print(f"   API Docs: {base_url}/docs")
    print(f"\n🎯 Next steps:")
    print(f"   1. Open http://localhost:3002 in your browser")
    print(f"   2. Try analyzing a Google Scholar profile")
    print(f"   3. Check backend logs: tail -f backend/backend.log")

if __name__ == "__main__":
    test_api()