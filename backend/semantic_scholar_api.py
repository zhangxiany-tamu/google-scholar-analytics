import requests
import time
import logging
from typing import Dict, List, Optional
from collections import defaultdict
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)

class SemanticScholarClassifier:
    """
    Use Semantic Scholar API to classify research papers by field of study
    Optimized for practical use with smart sampling and caching
    """
    
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.session = requests.Session()
        self.cache = {}  # Simple in-memory cache
        
    def search_paper_by_title(self, title: str) -> Optional[Dict]:
        """Search for a paper by title and get its fields of study"""
        try:
            # Clean title for search
            clean_title = title.replace('"', '').strip()
            if len(clean_title) < 10:  # Skip very short titles
                return None
                
            url = f"{self.base_url}/paper/search"
            params = {
                'query': clean_title,
                'limit': 1,
                'fields': 'title,fieldsOfStudy,citationCount,year'
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    paper = data['data'][0]
                    
                    # Check if title similarity is reasonable
                    if self._title_similarity(title, paper.get('title', '')) > 0.7:
                        return paper
                        
            elif response.status_code == 429:  # Rate limited
                logger.warning("Rate limited, waiting...")
                time.sleep(1)
                return self.search_paper_by_title(title)  # Retry
                
        except Exception as e:
            logger.error(f"Error searching for paper '{title}': {str(e)}")
            
        return None
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """Simple title similarity check"""
        if not title1 or not title2:
            return 0.0
            
        # Convert to lowercase and split into words
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def classify_publications(self, publications: List[Dict]) -> Dict:
        """Classify publications using hybrid approach: API for sample + keywords for rest"""
        logger.info(f"Classifying {len(publications)} publications using hybrid approach")
        
        # Smart sampling: get top cited papers + recent papers
        sample_papers = self._get_representative_sample(publications)
        
        logger.info(f"Using Semantic Scholar API for {len(sample_papers)} representative papers")
        
        # Classify sample using API
        api_results = self._classify_sample_with_api(sample_papers)
        
        # Use API results to improve keyword classification for all papers
        enhanced_results = self._enhance_keyword_classification(publications, api_results)
        
        return enhanced_results
    
    def _get_representative_sample(self, publications: List[Dict], max_sample=30) -> List[Dict]:
        """Get a representative sample of papers for API classification"""
        if len(publications) <= max_sample:
            return publications
        
        # Sort by citations (descending) and get top cited
        sorted_by_citations = sorted(publications, key=lambda p: p.get('citation_count', 0), reverse=True)
        top_cited = sorted_by_citations[:max_sample//2]
        
        # Sort by year (descending) and get recent papers
        sorted_by_year = sorted(publications, key=lambda p: p.get('year', 0), reverse=True)
        recent_papers = sorted_by_year[:max_sample//2]
        
        # Combine and deduplicate
        sample = []
        seen_titles = set()
        
        for paper in top_cited + recent_papers:
            title = paper.get('title', '')
            if title and title not in seen_titles:
                sample.append(paper)
                seen_titles.add(title)
                
        return sample[:max_sample]
    
    def _classify_sample_with_api(self, sample_papers: List[Dict]) -> Dict:
        """Classify sample papers using Semantic Scholar API"""
        field_counts = defaultdict(int)
        classified_papers = defaultdict(list)
        api_success_count = 0
        
        for i, pub in enumerate(sample_papers):
            title = pub.get('title', '')
            if not title:
                continue
            
            # Check cache first
            if title in self.cache:
                paper_data = self.cache[title]
            else:
                # Rate limiting - be more conservative
                if i > 0:
                    time.sleep(0.2)  # 200ms delay between requests
                
                paper_data = self.search_paper_by_title(title)
                self.cache[title] = paper_data  # Cache result
            
            if paper_data and paper_data.get('fieldsOfStudy'):
                api_success_count += 1
                fields = paper_data['fieldsOfStudy']
                
                # Get the most specific field
                primary_field = fields[-1] if fields else 'Unknown'
                
                field_counts[primary_field] += 1
                classified_papers[primary_field].append({
                    'title': pub.get('title', ''),
                    'year': pub.get('year'),
                    'citations': pub.get('citation_count', 0),
                    'semantic_scholar_fields': fields,
                    'is_sample': True
                })
                
                logger.debug(f"API classified '{title}' as: {primary_field}")
            else:
                field_counts['Unclassified'] += 1
                classified_papers['Unclassified'].append({
                    'title': pub.get('title', ''),
                    'year': pub.get('year'),
                    'citations': pub.get('citation_count', 0),
                    'reason': 'Not found in Semantic Scholar',
                    'is_sample': True
                })
        
        logger.info(f"API classified {api_success_count}/{len(sample_papers)} sample papers")
        
        return {
            'field_counts': field_counts,
            'classified_papers': classified_papers,
            'api_success_count': api_success_count,
            'sample_size': len(sample_papers)
        }
    
    def _enhance_keyword_classification(self, all_publications: List[Dict], api_results: Dict) -> Dict:
        """Use API results to enhance keyword-based classification for all papers"""
        from analysis_engine import ProfileAnalyzer
        
        # Create a temporary analyzer for keyword classification
        analyzer = ProfileAnalyzer(use_semantic_scholar=False)
        keyword_results = analyzer._keyword_based_classification(all_publications)
        
        # If API found meaningful classifications, use them to adjust keyword results
        if api_results['api_success_count'] > 0:
            # Map semantic scholar fields to our keyword domains
            field_mapping = {
                'Computer Science': 'Machine Learning & AI',
                'Mathematics': 'Statistics & Probability',
                'Statistics': 'Statistics & Probability',
                'Biology': 'Bioinformatics & Genomics',
                'Medicine': 'Bioinformatics & Genomics',
                'Environmental Science': 'Environmental & Ecological',
                'Economics': 'Economics & Finance',
                'Psychology': 'Social & Behavioral Sciences',
                'Engineering': 'Software & Tools'
            }
            
            # Adjust keyword results based on API findings
            api_field_counts = api_results['field_counts']
            
            # If API found specific fields, boost corresponding keyword domains
            for api_field, count in api_field_counts.items():
                if api_field in field_mapping:
                    keyword_domain = field_mapping[api_field]
                    if keyword_domain in keyword_results['area_percentages']:
                        # Boost this domain by 20% if found by API
                        current_percentage = keyword_results['area_percentages'][keyword_domain]
                        boosted_percentage = min(current_percentage * 1.2, 100)
                        keyword_results['area_percentages'][keyword_domain] = round(boosted_percentage, 1)
        
        # Re-normalize percentages
        total_percentage = sum(keyword_results['area_percentages'].values())
        if total_percentage > 0:
            for domain in keyword_results['area_percentages']:
                keyword_results['area_percentages'][domain] = round(
                    keyword_results['area_percentages'][domain] / total_percentage * 100, 1
                )
        
        # Sort by percentage again
        sorted_areas = sorted(keyword_results['area_percentages'].items(), key=lambda x: x[1], reverse=True)
        
        return {
            'area_percentages': dict(sorted_areas),
            'area_papers': keyword_results['area_papers'],
            'primary_area': sorted_areas[0][0] if sorted_areas else None,
            'interdisciplinary_score': keyword_results['interdisciplinary_score'],
            'method': 'hybrid_semantic_scholar_keywords',
            'api_success_rate': round(api_results['api_success_count'] / api_results['sample_size'] * 100, 1) if api_results['sample_size'] > 0 else 0,
            'total_classified': len(all_publications),
            'api_sample_size': api_results['sample_size']
        }

# Example of field classifications you might get:
EXAMPLE_FIELDS = [
    "Computer Science",
    "Mathematics", 
    "Statistics",
    "Biology",
    "Medicine",
    "Physics",
    "Chemistry",
    "Economics",
    "Psychology",
    "Environmental Science",
    "Materials Science",
    "Engineering"
]