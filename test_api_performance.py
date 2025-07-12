#!/usr/bin/env python3
"""
Test API performance with concurrent scraping
"""
import requests
import time

def test_api_performance():
    base_url = "http://localhost:8000"
    
    print("🚀 Testing API Performance with Concurrent Scraping")
    print("=" * 55)
    
    # Example test - replace with a real Google Scholar ID
    test_id = input("Enter a Google Scholar user ID to test API performance: ").strip()
    
    if not test_id:
        print("Please provide a valid Google Scholar user ID")
        return
    
    print(f"\n📊 Testing API performance for user: {test_id}")
    
    # Test profile import (includes concurrent scraping)
    print("\n1. Testing profile import with concurrent scraping...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{base_url}/api/scholar/import/{test_id}",
            timeout=120  # 2 minute timeout
        )
        
        import_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Profile imported successfully in {import_time:.2f} seconds")
            print(f"   Profile: {data.get('name', 'Unknown')}")
            print(f"   Citations: {data.get('total_citations', 0)}")
            
            profile_id = data['id']
            
            # Test complete analysis
            print(f"\n2. Testing complete analysis...")
            start_time = time.time()
            
            response = requests.get(f"{base_url}/api/analysis/{profile_id}/complete")
            analysis_time = time.time() - start_time
            
            if response.status_code == 200:
                analysis = response.json()
                pub_count = analysis.get('publications_count', 0)
                print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
                print(f"   Publications analyzed: {pub_count}")
                print(f"   Total time: {import_time + analysis_time:.2f} seconds")
                
                # Show concurrent scraping benefits
                print(f"\n🎯 Performance Summary:")
                print(f"   • Concurrent scraping enabled: ✅")
                print(f"   • API response time: {import_time:.2f}s")
                print(f"   • Analysis time: {analysis_time:.2f}s") 
                print(f"   • Total publications: {pub_count}")
                
                if pub_count > 0:
                    print(f"   • Time per publication: {(import_time + analysis_time) / pub_count:.3f}s")
                
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate slow scraping")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_performance()