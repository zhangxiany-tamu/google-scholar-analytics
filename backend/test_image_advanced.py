#!/usr/bin/env python3

import sys
import time
import requests
from urllib.parse import urljoin

def test_direct_image_access(user_id):
    """Test direct access to Google Scholar profile image"""
    
    # Mimic a real browser more closely
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # First, visit the main profile page to establish session
    profile_url = f"https://scholar.google.com/citations?user={user_id}&hl=en"
    print(f"1. Visiting profile page: {profile_url}")
    
    try:
        response = session.get(profile_url)
        print(f"   Profile page status: {response.status_code}")
        
        if response.status_code == 200:
            print("   Profile page loaded successfully")
            # Add delay to be respectful
            time.sleep(3)
            
            # Now try different image URL formats
            image_urls = [
                f"https://scholar.googleusercontent.com/citations?view_op=view_photo&user={user_id}&citpid=11",
                f"https://scholar.googleusercontent.com/citations?view_op=view_photo&user={user_id}",
                f"https://scholar.google.com/citations?view_op=view_photo&user={user_id}&citpid=11",
                f"https://scholar.google.com/citations?view_op=view_photo&user={user_id}",
            ]
            
            for i, img_url in enumerate(image_urls, 2):
                print(f"\n{i}. Testing image URL: {img_url}")
                try:
                    img_response = session.head(img_url)
                    print(f"   Status: {img_response.status_code}")
                    print(f"   Content-Type: {img_response.headers.get('content-type', 'Unknown')}")
                    print(f"   Content-Length: {img_response.headers.get('content-length', 'Unknown')} bytes")
                    
                    if img_response.status_code == 200 and 'image' in img_response.headers.get('content-type', ''):
                        print(f"   ✓ SUCCESS: Found working image URL!")
                        return img_url
                    elif img_response.status_code == 429:
                        print(f"   ✗ Rate limited (429)")
                    else:
                        print(f"   ✗ Not an image or error")
                        
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Add delay between requests
                time.sleep(2)
        else:
            print(f"   ✗ Profile page failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error accessing profile: {e}")
    
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_image_advanced.py <scholar_user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    result = test_direct_image_access(user_id)
    
    if result:
        print(f"\n🎉 Working image URL found: {result}")
    else:
        print(f"\n❌ No working image URL found. Google Scholar may be blocking automated access to images.") 