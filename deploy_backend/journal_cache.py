"""
Journal classification cache to improve performance
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class JournalCache:
    """
    Cache for journal classifications to avoid repeated API calls
    """
    
    def __init__(self, cache_file: str = "journal_cache.json", cache_duration_days: int = 7):
        self.cache_file = cache_file
        self.cache_duration = timedelta(days=cache_duration_days)
        self.cache = {}
        self.load_cache()
    
    def load_cache(self):
        """Load cache from file if it exists and is not expired"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    
                cache_date = datetime.fromisoformat(data.get('cache_date', '1970-01-01'))
                if datetime.now() - cache_date < self.cache_duration:
                    self.cache = data.get('journal_domains', {})
                    return True
                    
            except Exception as e:
                print(f"Error loading cache: {e}")
                
        return False
    
    def save_cache(self, journal_domains: Dict[str, List[str]]):
        """Save journal domains to cache"""
        try:
            data = {
                'cache_date': datetime.now().isoformat(),
                'journal_domains': journal_domains
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_cached_domains(self) -> Optional[Dict[str, List[str]]]:
        """Get cached journal domains if available"""
        return self.cache if self.cache else None
    
    def is_cache_valid(self) -> bool:
        """Check if cache is valid and not expired"""
        return bool(self.cache)