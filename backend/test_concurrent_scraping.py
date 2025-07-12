#!/usr/bin/env python3
"""
Test script for concurrent vs sequential scraping performance
"""

import time
import logging
from scholar_scraper import GoogleScholarScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scraping_performance(user_id: str, limit: int = 60):
    """
    Test both concurrent and sequential scraping methods
    """
    scraper = GoogleScholarScraper()
    
    print(f"\n=== Testing scraping performance for user {user_id} ===")
    print(f"Scraping limit: {limit} publications")
    
    # Test concurrent method
    print("\n1. Testing CONCURRENT scraping method...")
    start_time = time.time()
    try:
        concurrent_pubs = scraper.scrape_publications(user_id, limit)
        concurrent_time = time.time() - start_time
        concurrent_count = len(concurrent_pubs)
        print(f"✅ Concurrent method completed in {concurrent_time:.2f} seconds")
        print(f"   Publications found: {concurrent_count}")
    except Exception as e:
        print(f"❌ Concurrent method failed: {str(e)}")
        concurrent_time = float('inf')
        concurrent_count = 0
    
    # Wait a bit between tests
    time.sleep(5)
    
    # Test legacy sequential method
    print("\n2. Testing SEQUENTIAL (legacy) scraping method...")
    start_time = time.time()
    try:
        sequential_pubs = scraper.scrape_publications_legacy(user_id, limit)
        sequential_time = time.time() - start_time
        sequential_count = len(sequential_pubs)
        print(f"✅ Sequential method completed in {sequential_time:.2f} seconds")
        print(f"   Publications found: {sequential_count}")
    except Exception as e:
        print(f"❌ Sequential method failed: {str(e)}")
        sequential_time = float('inf')
        sequential_count = 0
    
    # Compare results
    print(f"\n=== Performance Comparison ===")
    if concurrent_time < float('inf') and sequential_time < float('inf'):
        speedup = sequential_time / concurrent_time
        print(f"Concurrent time: {concurrent_time:.2f}s ({concurrent_count} pubs)")
        print(f"Sequential time: {sequential_time:.2f}s ({sequential_count} pubs)")
        print(f"🚀 Speedup: {speedup:.2f}x faster")
        
        if abs(concurrent_count - sequential_count) <= 2:  # Allow small differences
            print("✅ Publication counts match (within tolerance)")
        else:
            print(f"⚠️  Publication count difference: {abs(concurrent_count - sequential_count)}")
    else:
        print("⚠️  Could not complete comparison due to errors")

if __name__ == "__main__":
    # Test with a sample user ID - replace with actual Google Scholar ID
    # You can get this from any Google Scholar profile URL
    test_user_id = input("Enter a Google Scholar user ID to test (or press Enter for demo): ").strip()
    
    if not test_user_id:
        print("Please provide a valid Google Scholar user ID")
        print("Example: 'ABC123XYZ' or full URL like 'https://scholar.google.com/citations?hl=en&user=ABC123XYZ'")
        exit(1)
    
    try:
        test_scraping_performance(test_user_id, limit=60)  # Test with 60 publications
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()