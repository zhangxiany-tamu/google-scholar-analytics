#!/usr/bin/env python3

import sys
import time
import requests
from PIL import Image
import io

def check_image_dimensions(user_id):
    """Download and check the actual dimensions of Google Scholar profile image"""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://scholar.google.com/citations?user={user_id}&hl=en',
    })
    
    # First visit profile page
    profile_url = f"https://scholar.google.com/citations?user={user_id}&hl=en"
    print(f"Visiting profile page...")
    session.get(profile_url)
    time.sleep(2)
    
    # Now get the image
    image_url = f"https://scholar.googleusercontent.com/citations?view_op=view_photo&user={user_id}&citpid=11"
    print(f"Downloading image: {image_url}")
    
    try:
        response = session.get(image_url)
        
        if response.status_code == 200:
            print(f"✓ Image downloaded successfully")
            print(f"  File size: {len(response.content)} bytes ({len(response.content)/1024:.1f} KB)")
            print(f"  Content-Type: {response.headers.get('content-type')}")
            
            # Load image and check dimensions
            image = Image.open(io.BytesIO(response.content))
            width, height = image.size
            print(f"  Dimensions: {width} x {height} pixels")
            print(f"  Format: {image.format}")
            print(f"  Mode: {image.mode}")
            
            # Calculate if this is high or low resolution
            if width <= 80 and height <= 80:
                quality = "Very Low Resolution (thumbnail)"
            elif width <= 150 and height <= 150:
                quality = "Low Resolution"
            elif width <= 300 and height <= 300:
                quality = "Medium Resolution"
            else:
                quality = "High Resolution"
                
            print(f"  Quality Assessment: {quality}")
            
            return {
                'width': width,
                'height': height,
                'size_bytes': len(response.content),
                'quality': quality
            }
            
        else:
            print(f"✗ Failed to download image: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_image_dimensions.py <scholar_user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    result = check_image_dimensions(user_id)
    
    if result:
        print(f"\n📊 CONCLUSION:")
        print(f"Google Scholar provides profile images at {result['width']}x{result['height']} resolution.")
        print(f"This is considered {result['quality'].lower()}.")
        if result['width'] <= 150:
            print("❌ Unfortunately, Google Scholar does not provide high-resolution profile images.")
            print("The images are intentionally kept small, likely for privacy and bandwidth reasons.")
        else:
            print("✅ The image quality should be acceptable for display.")
    else:
        print("\n❌ Could not determine image quality.") 