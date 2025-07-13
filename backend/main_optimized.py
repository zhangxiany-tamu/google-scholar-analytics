from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import uvicorn
import os
from datetime import datetime
import logging
import asyncio
import concurrent.futures
import functools
import re
from urllib.parse import unquote

# Lazy imports for heavy libraries - only import when needed
import importlib
import threading

# Global cache for heavy modules
_heavy_modules = {}
_import_lock = threading.Lock()

def get_heavy_module(module_name: str):
    """Lazy import heavy modules with caching"""
    with _import_lock:
        if module_name not in _heavy_modules:
            if module_name == 'pandas':
                import pandas as pd
                _heavy_modules['pandas'] = pd
            elif module_name == 'numpy':
                import numpy as np
                _heavy_modules['numpy'] = np
            elif module_name == 'sklearn':
                import sklearn
                _heavy_modules['sklearn'] = sklearn
        return _heavy_modules[module_name]

# Light imports that are always needed
from scholar_scraper import GoogleScholarScraper
from cache_manager import (
    cache_publications, get_cached_publications,
    cache_analysis, get_cached_analysis,
    cache_profile, get_cached_profile,
    cache_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pre-warm heavy libraries in background during startup
def pre_warm_libraries():
    """Pre-load heavy libraries in background thread"""
    try:
        logger.info("🔥 Pre-warming heavy libraries...")
        
        # Import in background
        import pandas as pd
        import numpy as np
        import sklearn
        
        # Cache them
        _heavy_modules['pandas'] = pd
        _heavy_modules['numpy'] = np
        _heavy_modules['sklearn'] = sklearn
        
        logger.info("✅ Heavy libraries pre-warmed successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to pre-warm libraries: {e}")

# Import analysis engine only when needed
def get_analyzer():
    """Lazy import ProfileAnalyzer"""
    if 'ProfileAnalyzer' not in globals():
        from analysis_engine import ProfileAnalyzer
        globals()['ProfileAnalyzer'] = ProfileAnalyzer
    return globals()['ProfileAnalyzer']

async def get_publications_data(profile_id: str, user_id: str) -> List[Dict]:
    """Helper function to get publications data with caching"""
    # Try cache first
    publications_data = get_cached_publications(profile_id)
    if publications_data:
        logger.info(f"📥 Using cached publications for {profile_id}")
        return publications_data
    
    logger.info(f"📤 Scraping publications for {profile_id}")
    scraper = GoogleScholarScraper()
    
    # Scrape publications using concurrent method with fallback
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        try:
            # Try concurrent scraping first
            publications_data = await loop.run_in_executor(executor, scraper.scrape_publications, user_id, 200)
        except Exception as e:
            logger.warning(f"Concurrent scraping failed, falling back to legacy method: {str(e)}")
            # Fallback to sequential scraping
            publications_data = await loop.run_in_executor(executor, scraper.scrape_publications_legacy, user_id, 200)
    
    # Cache the result
    cache_publications(profile_id, publications_data, ttl=1800)
    logger.info(f"💾 Cached publications for {profile_id}: {len(publications_data)} items")
    
    return publications_data

app = FastAPI(
    title="Google Scholar Profile Analyzer API",
    description="API for analyzing Google Scholar profiles with comprehensive statistics",
    version="1.0.0"
)

# Start pre-warming libraries in background
threading.Thread(target=pre_warm_libraries, daemon=True).start()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://localhost:3002",
        "https://scholar-frontend-771064042567.us-central1.run.app",
        "https://*.run.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# [Rest of the code remains the same...]
# Just showing the optimization pattern here

@app.get("/")
async def root():
    return {"message": "Google Scholar Profile Analyzer API - Optimized", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    # Check if heavy libraries are loaded
    libraries_loaded = all(mod in _heavy_modules for mod in ['pandas', 'numpy', 'sklearn'])
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "libraries_preloaded": libraries_loaded
    }

if __name__ == "__main__":
    uvicorn.run(
        "main_optimized:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )