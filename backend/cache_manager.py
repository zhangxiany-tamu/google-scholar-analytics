#!/usr/bin/env python3
"""
Redis-based caching manager for Google Scholar Profile Analyzer
"""

import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import pickle
import functools

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager with intelligent key generation and TTL management"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        """
        Initialize cache manager
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (1 hour)
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            # Fallback to no-op cache
            self.redis_client = None
        
        self.default_ttl = default_ttl
        self.prefix = "scholar_analyzer:"
    
    def _generate_key(self, namespace: str, identifier: str, params: Dict = None) -> str:
        """Generate a cache key with optional parameter hashing"""
        key_parts = [self.prefix, namespace, identifier]
        
        if params:
            # Sort params for consistent hashing
            param_str = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return ":".join(key_parts)
    
    def get(self, namespace: str, identifier: str, params: Dict = None) -> Optional[Any]:
        """Get cached data"""
        if not self.redis_client:
            return None
        
        key = self._generate_key(namespace, identifier, params)
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                # Try JSON first, fallback to pickle
                try:
                    result = json.loads(cached_data)
                    logger.debug(f"📥 Cache HIT (JSON): {key}")
                    return result
                except (json.JSONDecodeError, UnicodeDecodeError):
                    try:
                        result = pickle.loads(cached_data)
                        logger.debug(f"📥 Cache HIT (pickle): {key}")
                        return result
                    except Exception:
                        logger.warning(f"⚠️  Cache data corrupted, deleting: {key}")
                        self.redis_client.delete(key)
                        return None
            else:
                logger.debug(f"📤 Cache MISS: {key}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Cache get error: {e}")
            return None
    
    def set(self, namespace: str, identifier: str, data: Any, params: Dict = None, ttl: Optional[int] = None) -> bool:
        """Set cached data with TTL"""
        if not self.redis_client:
            return False
        
        key = self._generate_key(namespace, identifier, params)
        cache_ttl = ttl or self.default_ttl
        
        try:
            # Try JSON serialization first (more readable), fallback to pickle
            try:
                serialized_data = json.dumps(data, default=str)  # Convert datetime etc to string
                encoding = "json"
            except (TypeError, ValueError):
                serialized_data = pickle.dumps(data)
                encoding = "pickle"
            
            success = self.redis_client.setex(key, cache_ttl, serialized_data)
            
            if success:
                logger.debug(f"💾 Cache SET ({encoding}): {key} (TTL: {cache_ttl}s)")
                return True
            else:
                logger.error(f"❌ Cache set failed: {key}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Cache set error: {e}")
            return False
    
    def delete(self, namespace: str, identifier: str, params: Dict = None) -> bool:
        """Delete cached data"""
        if not self.redis_client:
            return False
        
        key = self._generate_key(namespace, identifier, params)
        
        try:
            deleted = self.redis_client.delete(key)
            if deleted:
                logger.debug(f"🗑️  Cache DELETE: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.redis_client:
            return 0
        
        try:
            full_pattern = f"{self.prefix}{pattern}"
            keys = self.redis_client.keys(full_pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️  Cache DELETE pattern '{full_pattern}': {deleted} keys")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"❌ Cache delete pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            info = self.redis_client.info()
            
            # Count our keys
            our_keys = self.redis_client.keys(f"{self.prefix}*")
            
            return {
                "status": "connected",
                "total_keys": len(our_keys),
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "hit_rate": "calculated separately",
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"❌ Cache stats error: {e}")
            return {"status": "error", "error": str(e)}

# Global cache instance
cache_manager = CacheManager()

def cache_result(namespace: str, ttl: int = 3600, use_params: bool = True):
    """
    Decorator to cache function results
    
    Args:
        namespace: Cache namespace (e.g., 'analysis', 'publications')
        ttl: Time to live in seconds
        use_params: Whether to include function parameters in cache key
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache identifier
            if args and hasattr(args[0], '__class__'):
                # Instance method - skip 'self' in key generation
                identifier_args = args[1:]
            else:
                identifier_args = args
            
            identifier = f"{func.__name__}_{hash(str(identifier_args))}"
            params = kwargs if use_params else None
            
            # Try to get from cache first
            cached_result = cache_manager.get(namespace, identifier, params)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            start_time = datetime.now()
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Cache the result
            cache_manager.set(namespace, identifier, result, params, ttl)
            
            logger.info(f"🔄 Function executed and cached: {func.__name__} ({execution_time:.2f}s)")
            return result
        
        return wrapper
    return decorator

# Convenience functions for common operations
def cache_publications(profile_id: str, data: List[Dict], ttl: int = 1800):
    """Cache publication data (30 minutes TTL)"""
    return cache_manager.set("publications", profile_id, data, ttl=ttl)

def get_cached_publications(profile_id: str) -> Optional[List[Dict]]:
    """Get cached publication data"""
    return cache_manager.get("publications", profile_id)

def cache_analysis(profile_id: str, analysis_type: str, data: Dict, ttl: int = 3600):
    """Cache analysis results (1 hour TTL)"""
    return cache_manager.set("analysis", f"{profile_id}_{analysis_type}", data, ttl=ttl)

def get_cached_analysis(profile_id: str, analysis_type: str) -> Optional[Dict]:
    """Get cached analysis results"""
    return cache_manager.get("analysis", f"{profile_id}_{analysis_type}")

def cache_profile(profile_id: str, data: Dict, ttl: int = 1800):
    """Cache profile data (30 minutes TTL)"""
    return cache_manager.set("profiles", profile_id, data, ttl=ttl)

def get_cached_profile(profile_id: str) -> Optional[Dict]:
    """Get cached profile data"""
    return cache_manager.get("profiles", profile_id)

def invalidate_profile_cache(profile_id: str):
    """Invalidate all cache entries for a profile"""
    patterns = [
        f"publications:{profile_id}*",
        f"analysis:{profile_id}*", 
        f"profiles:{profile_id}*"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        total_deleted += cache_manager.delete_pattern(pattern)
    
    logger.info(f"🗑️  Invalidated cache for profile {profile_id}: {total_deleted} entries")
    return total_deleted