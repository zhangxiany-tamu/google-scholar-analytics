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
from scholar_scraper import GoogleScholarScraper
from analysis_engine import ProfileAnalyzer
from cache_manager import (
    cache_publications, get_cached_publications,
    cache_analysis, get_cached_analysis,
    cache_profile, get_cached_profile,
    cache_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://localhost:3002",
        "https://scholar-frontend-771064042567.us-central1.run.app",
        "https://*.run.app"
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Pydantic models
class ScholarProfileRequest(BaseModel):
    google_scholar_id: str

class ScholarProfileResponse(BaseModel):
    id: str
    name: str
    affiliation: Optional[str] = None
    interests: List[str] = []
    h_index: Optional[int] = None
    i10_index: Optional[int] = None
    total_citations: Optional[int] = None
    profile_image_url: Optional[str] = None
    citation_timeline: Optional[Dict] = None
    last_updated: datetime

class Publication(BaseModel):
    id: str
    title: str
    authors: str
    venue: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = 0
    google_scholar_url: Optional[str] = None

class AnalysisResult(BaseModel):
    profile_id: str
    analysis_type: str
    results: Dict[str, Any]
    computed_at: datetime

# Mock data for development
MOCK_PROFILE = {
    "id": "mock_profile_1",
    "name": "Dr. Jane Smith",
    "affiliation": "Stanford University",
    "interests": ["Machine Learning", "Natural Language Processing", "Computer Vision"],
    "h_index": 35,
    "i10_index": 52,
    "total_citations": 2847,
    "profile_image_url": None,
    "last_updated": datetime.now()
}

MOCK_PUBLICATIONS = [
    {
        "id": "pub_1",
        "title": "Advanced Neural Networks for Text Classification",
        "authors": "Jane Smith, John Doe, Alice Johnson",
        "venue": "ICML 2023",
        "year": 2023,
        "citation_count": 45,
        "google_scholar_url": "https://scholar.google.com/citations?view_op=view_citation&hl=en&user=ABC123&citation_for_view=ABC123:def456"
    },
    {
        "id": "pub_2", 
        "title": "Deep Learning Approaches to Computer Vision",
        "authors": "Alice Johnson, Jane Smith",
        "venue": "CVPR 2022",
        "year": 2022,
        "citation_count": 127,
        "google_scholar_url": "https://scholar.google.com/citations?view_op=view_citation&hl=en&user=ABC123&citation_for_view=ABC123:ghi789"
    }
]

# Routes
@app.get("/")
async def root():
    return {"message": "Google Scholar Profile Analyzer API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/api/scholar/import/{google_scholar_id:path}", response_model=ScholarProfileResponse)
async def import_scholar_profile(google_scholar_id: str):
    """Import and analyze a Google Scholar profile"""
    try:
        # Decode URL if needed
        google_scholar_id = unquote(google_scholar_id)
        logger.info(f"Importing Google Scholar profile: {google_scholar_id}")
        
        # Initialize scraper
        scraper = GoogleScholarScraper()
        
        # Extract user ID from URL if provided
        if google_scholar_id.startswith('http'):
            google_scholar_id = scraper.extract_user_id(google_scholar_id)
        
        # Scrape profile data
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            profile_data = await loop.run_in_executor(executor, scraper.scrape_profile, google_scholar_id)
        
        # Create response with unique ID
        response_data = {
            "id": f"profile_{google_scholar_id}",
            "name": profile_data.get('name', 'Unknown'),
            "affiliation": profile_data.get('affiliation'),
            "interests": profile_data.get('interests', []),
            "h_index": profile_data.get('h_index'),
            "i10_index": profile_data.get('i10_index'),
            "total_citations": profile_data.get('total_citations'),
            "profile_image_url": profile_data.get('profile_image_url'),
            "citation_timeline": profile_data.get('citation_timeline'),
            "last_updated": datetime.now()
        }
        
        return ScholarProfileResponse(**response_data)
    
    except Exception as e:
        logger.error(f"Error importing profile {google_scholar_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import profile: {str(e)}"
        )

@app.get("/api/scholar/profile/{profile_id}", response_model=ScholarProfileResponse)
async def get_scholar_profile(profile_id: str):
    """Get scholar profile by ID"""
    try:
        # TODO: Fetch from database
        profile_data = MOCK_PROFILE.copy()
        profile_data["id"] = profile_id
        
        return ScholarProfileResponse(**profile_data)
    
    except Exception as e:
        logger.error(f"Error fetching profile {profile_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

@app.get("/api/publications/{profile_id}", response_model=List[Publication])
async def get_publications(profile_id: str):
    """Get publications for a profile with caching"""
    try:
        logger.info(f"Fetching publications for profile: {profile_id}")
        
        # Check cache first
        cached_publications = get_cached_publications(profile_id)
        if cached_publications:
            logger.info(f"📥 Cache HIT: Publications for {profile_id}")
            # Convert cached data to response format
            publications = []
            for i, pub in enumerate(cached_publications):
                publications.append(Publication(
                    id=f"pub_{i+1}",
                    title=pub.get('title', ''),
                    authors=pub.get('authors', ''),
                    venue=pub.get('venue', ''),
                    year=pub.get('year'),
                    citation_count=pub.get('citation_count', 0),
                    google_scholar_url=pub.get('google_scholar_url', '')
                ))
            return publications
        
        logger.info(f"📤 Cache MISS: Scraping publications for {profile_id}")
        
        # Extract user ID from profile ID
        user_id = profile_id.replace('profile_', '')
        
        # Initialize scraper
        scraper = GoogleScholarScraper()
        
        # Scrape publications using concurrent method with fallback
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            try:
                # Try concurrent scraping first
                logger.info("Using concurrent scraping method")
                publications_data = await loop.run_in_executor(executor, scraper.scrape_publications, user_id, 200)
            except Exception as e:
                logger.warning(f"Concurrent scraping failed, falling back to legacy method: {str(e)}")
                # Fallback to sequential scraping
                publications_data = await loop.run_in_executor(executor, scraper.scrape_publications_legacy, user_id, 200)
        
        # Cache the raw publication data
        cache_publications(profile_id, publications_data, ttl=1800)  # 30 minutes
        logger.info(f"💾 Cached publications for {profile_id}: {len(publications_data)} items")
        
        # Convert to response format
        publications = []
        for i, pub in enumerate(publications_data):
            publications.append(Publication(
                id=f"pub_{i+1}",
                title=pub.get('title', ''),
                authors=pub.get('authors', ''),
                venue=pub.get('venue', ''),
                year=pub.get('year'),
                citation_count=pub.get('citation_count', 0),
                google_scholar_url=pub.get('google_scholar_url', '')
            ))
        
        return publications
    
    except Exception as e:
        logger.error(f"Error fetching publications for {profile_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch publications"
        )

@app.get("/api/analysis/{profile_id}/overview", response_model=AnalysisResult)
async def get_analysis_overview(profile_id: str):
    """Get overview analysis for a profile with caching"""
    try:
        logger.info(f"Generating analysis overview for profile: {profile_id}")
        
        # Check cache first
        cached_analysis = get_cached_analysis(profile_id, "overview")
        if cached_analysis:
            logger.info(f"📥 Cache HIT: Overview analysis for {profile_id}")
            return AnalysisResult(
                profile_id=profile_id,
                analysis_type="overview",
                results=cached_analysis,
                computed_at=datetime.now()
            )
        
        logger.info(f"📤 Cache MISS: Computing overview analysis for {profile_id}")
        
        # Extract user ID from profile ID
        user_id = profile_id.replace('profile_', '')
        
        # Initialize scraper and analyzer
        scraper = GoogleScholarScraper()
        analyzer = ProfileAnalyzer()
        
        # Try to get cached publications first
        publications_data = get_cached_publications(profile_id)
        if not publications_data:
            # Get profile and publications data
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                profile_data = await loop.run_in_executor(executor, scraper.scrape_profile, user_id)
                try:
                    # Try concurrent scraping first
                    publications_data = await loop.run_in_executor(executor, scraper.scrape_publications, user_id, 200)
                except Exception as e:
                    logger.warning(f"Concurrent scraping failed, falling back to legacy method: {str(e)}")
                    # Fallback to sequential scraping
                    publications_data = await loop.run_in_executor(executor, scraper.scrape_publications_legacy, user_id, 200)
                
                # Cache publications for future use
                cache_publications(profile_id, publications_data, ttl=1800)
        else:
            logger.info(f"📥 Using cached publications for analysis")
            # Still need profile data
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                profile_data = await loop.run_in_executor(executor, scraper.scrape_profile, user_id)
        
        # Perform comprehensive analysis
        analysis = analyzer.analyze_profile_comprehensive(profile_data, publications_data)
        
        # Create overview summary
        basic_metrics = analysis.get('basic_metrics', {})
        authorship = analysis.get('authorship_analysis', {})
        research_areas = analysis.get('research_areas', {})
        
        overview_data = {
            **basic_metrics,
            'first_author_papers': authorship.get('first_author', {}).get('count', 0),
            'last_author_papers': authorship.get('last_author', {}).get('count', 0),
            'single_author_papers': authorship.get('single_author', {}).get('count', 0),
            'research_areas': research_areas.get('area_percentages', {}),
            'primary_research_area': research_areas.get('primary_area'),
            'interdisciplinary_score': research_areas.get('interdisciplinary_score', 0)
        }
        
        # Cache the analysis result
        cache_analysis(profile_id, "overview", overview_data, ttl=3600)  # 1 hour
        logger.info(f"💾 Cached overview analysis for {profile_id}")
        
        return AnalysisResult(
            profile_id=profile_id,
            analysis_type="overview",
            results=overview_data,
            computed_at=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Error generating analysis for {profile_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analysis"
        )

@app.get("/api/analysis/{profile_id}/authorship", response_model=AnalysisResult)
async def get_authorship_analysis(profile_id: str):
    """Get authorship analysis for a profile with caching"""
    try:
        logger.info(f"Generating authorship analysis for profile: {profile_id}")
        
        # Check cache first
        cached_analysis = get_cached_analysis(profile_id, "authorship")
        if cached_analysis:
            logger.info(f"📥 Cache HIT: Authorship analysis for {profile_id}")
            return AnalysisResult(
                profile_id=profile_id,
                analysis_type="authorship",
                results=cached_analysis,
                computed_at=datetime.now()
            )
        
        logger.info(f"📤 Cache MISS: Computing authorship analysis for {profile_id}")
        
        # Extract user ID from profile ID
        user_id = profile_id.replace('profile_', '')
        
        # Initialize analyzer
        analyzer = ProfileAnalyzer()
        
        # Try to use cached publications data
        publications_data = await get_publications_data(profile_id, user_id)
        
        # Get profile data (needed for analysis)
        scraper = GoogleScholarScraper()
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            profile_data = await loop.run_in_executor(executor, scraper.scrape_profile, user_id)
        
        # Perform comprehensive analysis
        analysis = analyzer.analyze_profile_comprehensive(profile_data, publications_data)
        
        # Extract authorship analysis
        authorship_data = analysis.get('authorship_analysis', {})
        
        # Cache the analysis result
        cache_analysis(profile_id, "authorship", authorship_data, ttl=3600)  # 1 hour
        logger.info(f"💾 Cached authorship analysis for {profile_id}")
        
        return AnalysisResult(
            profile_id=profile_id,
            analysis_type="authorship",
            results=authorship_data,
            computed_at=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Error generating authorship analysis for {profile_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorship analysis"
        )

@app.get("/api/analysis/{profile_id}/complete")
async def get_complete_analysis(profile_id: str, use_semantic_scholar: bool = False):
    """Get complete comprehensive analysis for a profile with caching"""
    try:
        logger.info(f"Generating complete analysis for profile: {profile_id}")
        
        # Create cache key with parameters
        cache_key = f"complete_{use_semantic_scholar}"
        
        # Check cache first
        cached_analysis = get_cached_analysis(profile_id, cache_key)
        if cached_analysis:
            logger.info(f"📥 Cache HIT: Complete analysis for {profile_id} (semantic_scholar={use_semantic_scholar})")
            return cached_analysis
        
        logger.info(f"📤 Cache MISS: Computing complete analysis for {profile_id} (semantic_scholar={use_semantic_scholar})")
        
        # Extract user ID from profile ID
        user_id = profile_id.replace('profile_', '')
        
        # Initialize analyzer
        analyzer = ProfileAnalyzer(use_semantic_scholar=use_semantic_scholar)
        
        # Try to use cached publications data
        publications_data = await get_publications_data(profile_id, user_id)
        
        # Get profile data (needed for analysis)
        scraper = GoogleScholarScraper()
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            profile_data = await loop.run_in_executor(executor, scraper.scrape_profile, user_id)
        
        # Perform comprehensive analysis
        complete_analysis = analyzer.analyze_profile_comprehensive(profile_data, publications_data)
        
        # Prepare response
        result = {
            "profile_id": profile_id,
            "profile_data": profile_data,
            "publications_count": len(publications_data),
            "analysis": complete_analysis
        }
        
        # Cache the complete analysis result
        cache_analysis(profile_id, cache_key, result, ttl=3600)  # 1 hour
        logger.info(f"💾 Cached complete analysis for {profile_id} (semantic_scholar={use_semantic_scholar})")
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating complete analysis for {profile_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate complete analysis: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )