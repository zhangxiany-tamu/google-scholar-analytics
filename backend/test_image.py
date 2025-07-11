#!/usr/bin/env python3

import sys
import logging
from scholar_scraper import GoogleScholarScraper

# Set up logging to see the image extraction process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_image_extraction(user_id):
    """Test image extraction for a given user ID"""
    scraper = GoogleScholarScraper()
    
    try:
        # Get profile data
        profile_data = scraper.scrape_profile(user_id)
        
        print(f"Profile: {profile_data.get('name', 'Unknown')}")
        print(f"Image URL: {profile_data.get('profile_image_url', 'No image found')}")
        
        if profile_data.get('profile_image_url'):
            # Test if the URL is accessible
            import requests
            response = requests.head(profile_data['profile_image_url'])
            print(f"Image URL status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Content-Length: {response.headers.get('content-length', 'Unknown')} bytes")
            
        return profile_data.get('profile_image_url')
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_image.py <scholar_user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    test_image_extraction(user_id) 